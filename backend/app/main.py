from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.deps import require_role
from app.models.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Multi-Tenant Grounded Advisory Assistant (GAA) API Engine for Wealth Management",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

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
