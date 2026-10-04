import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import app

def test_production_config_rejects_short_jwt_secret():
    """Validates that production environment fails startup if JWT_SECRET_KEY < 32 chars."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="short-secret-key",
        GROQ_API_KEY="gsk_real_production_key_12345678901234567890",
        POSTGRES_PASSWORD="SuperSecurePassword123!@#$%",
    )
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a secure"):
        s.validate_production_configuration()

def test_production_config_rejects_placeholder_jwt_secret():
    """Validates that production environment fails startup if JWT_SECRET_KEY has placeholder strings."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="wealthguard-production-jwt-secret-replace-with-secure-random-token",
        GROQ_API_KEY="gsk_real_production_key_12345678901234567890",
        POSTGRES_PASSWORD="SuperSecurePassword123!@#$%",
    )
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a secure"):
        s.validate_production_configuration()

def test_production_config_rejects_wildcard_cors():
    """Validates that wildcard '*' CORS origin is strictly forbidden in production."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        ALLOWED_ORIGINS="*",
        GROQ_API_KEY="gsk_real_production_key_12345678901234567890",
        POSTGRES_PASSWORD="SuperSecurePassword123!@#$%",
    )
    with pytest.raises(ValueError, match="Wildcard CORS origin"):
        s.validate_production_configuration()

def test_production_config_rejects_weak_postgres_password():
    """Validates that default or short PostgreSQL passwords (<24 chars) are rejected in production."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        DATABASE_URL="postgresql://postgres:postgres_secure_pass_987@postgres:5432/gaa_db",
        POSTGRES_PASSWORD="postgres_secure_pass_987",
        GROQ_API_KEY="gsk_real_production_key_12345678901234567890",
    )
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD must be a high-entropy string"):
        s.validate_production_configuration()

def test_production_config_rejects_placeholder_groq_api_key():
    """Validates that placeholder Groq API keys are rejected in production."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        DATABASE_URL="sqlite:///./data/app.db",
        LLM_PROVIDER="groq",
        GROQ_API_KEY="gsk_mock_test_key",
    )
    with pytest.raises(ValueError, match="Valid GROQ_API_KEY is required"):
        s.validate_production_configuration()

def test_production_config_valid_success():
    """Validates that production environment validates cleanly when all parameters are high entropy."""
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="c8f1e29a34b578d0f12a3b4c5d6e7f80123456789abcdef0123456789abcdef0",
        POSTGRES_PASSWORD="StrongAndSecurePassword2026!#$%",
        DATABASE_URL="postgresql://postgres:StrongAndSecurePassword2026!#$%@gaa_postgres:5432/gaa_db",
        ALLOWED_ORIGINS="https://wealthguard.yourbank.com",
        LLM_PROVIDER="groq",
        GROQ_API_KEY="gsk_production_live_api_key_valid_entropy_9999",
    )
    # Should not raise any ValueError
    s.validate_production_configuration()
    assert s.cors_origins_list == ["https://wealthguard.yourbank.com"]

def test_http_security_headers_present(client: TestClient):
    """Verifies that all OWASP HTTP security headers are returned on responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers["Permissions-Policy"]
    assert "microphone=()" in resp.headers["Permissions-Policy"]
    assert "geolocation=()" in resp.headers["Permissions-Policy"]
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]

def test_liveness_probe(client: TestClient):
    """Verifies /health/liveness returns 200 with status 'alive' and timestamp."""
    resp = client.get("/health/liveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "timestamp" in data

def test_readiness_probe(client: TestClient):
    """Verifies /health/readiness returns 200 with status 'ready', DB and vector store checks."""
    resp = client.get("/health/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "connected"
    assert data["checks"]["vector_store"] == "connected"
    assert "chroma_path" in data["checks"]

def test_query_length_boundary_4000_chars(client: TestClient):
    """Verifies that query with 4000 characters is accepted by schema, while 4001 characters is rejected."""
    # 4001 characters should trigger 422
    token_resp = client.post("/api/v1/auth/login", json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"})
    token = token_resp.json()["access_token"]

    too_long_query = "A" * 4001
    resp_bad = client.post(
        "/api/v1/chat/query",
        json={"query": too_long_query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_bad.status_code == 422

    # Semantic search with 4001 characters should also trigger 422
    resp_search_bad = client.post(
        "/api/v1/chat/search",
        json={"query": too_long_query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_search_bad.status_code == 422
