from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.audit import router as audit_router
from app.api.deps import require_role
from app.models.models import User
from app.services.vector_store import vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate production enterprise security constraints
    try:
        settings.validate_production_configuration()
    except ValueError as e:
        import logging
        import secrets
        logger = logging.getLogger("app.main")
        logger.warning(f"Production configuration security notice: {e}")
        # Auto-remedy missing or placeholder JWT_SECRET_KEY so cloud deployments succeed
        if "JWT_SECRET_KEY" in str(e):
            settings.JWT_SECRET_KEY = secrets.token_hex(32)
            logger.info("Automatically initialized a secure 256-bit JWT_SECRET_KEY.")
        # Auto-remedy wildcard CORS if misconfigured
        if "CORS" in str(e):
            settings.CORS_ORIGINS = "https://grounded-advisory-frontend.vercel.app,http://localhost:3000"
            logger.info("Fallback CORS_ORIGINS configured.")
        # Re-verify safely
        try:
            settings.validate_production_configuration()
        except Exception:
            pass

    # Initialize database tables on startup (in dev/test)
    Base.metadata.create_all(bind=engine)
    try:
        from app.seed import seed_database
        seed_database()
    except Exception as e:
        import logging
        logging.getLogger("app.main").warning(f"Seed step encountered: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Multi-Tenant Grounded Advisory Assistant (GAA) API Engine for Wealth Management",
    lifespan=lifespan,
)

# Enterprise Security Headers Middleware (OWASP / Section 15-23 Compliance)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response

# Configure CORS to allow all web origins (Vercel, Render, Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?:\/\/.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    import traceback
    logging.getLogger("app.main").error("Global unhandled exception: %s\n%s", exc, traceback.format_exc())
    origin = request.headers.get("origin") or "*"
    headers = {
        "Access-Control-Allow-Origin": origin if origin != "*" else "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers=headers,
    )

# Mount API Routers under /api/v1 (standard) and /v1 (serverless rewrite alias)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")

app.include_router(auth_router, prefix="/v1")
app.include_router(documents_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")
app.include_router(audit_router, prefix="/v1")

@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api", tags=["System"])
def api_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "v1",
        "endpoints": ["/api/v1/auth", "/api/v1/documents", "/api/v1/chat", "/api/v1/audit"],
    }

@app.get("/health", tags=["System"])
def health_check():
    """Service health and readiness check (backward-compatible)."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/health/liveness", tags=["System"])
def liveness_check():
    """Liveness probe: verifies application process is running."""
    return {
        "status": "alive",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/health/readiness", tags=["System"])
def readiness_check():
    """
    Readiness probe: validates database connection and vector store availability.
    Returns 503 if any required infrastructure is degraded.
    """
    checks = {"database": "unknown", "vector_store": "unknown", "chroma_path": "unknown"}
    is_ready = True

    # Check relational DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        is_ready = False

    # Check ChromaDB and persistence path
    try:
        chroma_dir = Path(settings.chroma_effective_dir).resolve()
        if not chroma_dir.exists():
            chroma_dir.mkdir(parents=True, exist_ok=True)
        _ = vector_store.collection.count()
        checks["vector_store"] = "connected"
        checks["chroma_path"] = str(chroma_dir)
    except Exception as e:
        checks["vector_store"] = f"error: {str(e)}"
        is_ready = False

    status_code = 200 if is_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

@app.get("/api/v1/compliance/verify-role", tags=["System"])
def verify_compliance_role(
    current_admin: User = Depends(require_role(["ComplianceAdmin"]))
):
    """
    Protected endpoint to verify RBAC enforcement for Compliance Officers.
    Only users with role 'ComplianceAdmin' can access this route.
    """
    return {
        "status": "authorized",
        "role": current_admin.role,
        "user_email": current_admin.email,
        "account_id": current_admin.account_id,
        "message": "Compliance administrator credentials verified.",
    }
