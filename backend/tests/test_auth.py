import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.models import Account, User, PasswordResetToken
from app.main import app

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables and seed test fixtures before each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed Accounts
    acc_central = Account(
        id="branch_12_central",
        branch_name="Central Branch #12",
        branch_code="BR-12",
    )
    acc_north = Account(
        id="branch_01_north",
        branch_name="North Branch #01",
        branch_code="BR-01",
    )
    db.add(acc_central)
    db.add(acc_north)
    db.commit()

    # Seed Users
    rm_user = User(
        id="usr_rm_test",
        account_id="branch_12_central",
        email="rm_test@wealth.bank.com",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test RM",
        role="RM",
        is_active=True,
    )
    compliance_user = User(
        id="usr_comp_test",
        account_id="branch_12_central",
        email="comp_test@wealth.bank.com",
        password_hash=get_password_hash("AdminPassword123!"),
        full_name="Test Compliance Officer",
        role="ComplianceAdmin",
        is_active=True,
    )
    north_rm_user = User(
        id="usr_north_rm_test",
        account_id="branch_01_north",
        email="north_rm@wealth.bank.com",
        password_hash=get_password_hash("NorthPassword123!"),
        full_name="North RM",
        role="RM",
        is_active=True,
    )
    db.add(rm_user)
    db.add(compliance_user)
    db.add(north_rm_user)
    db.commit()
    db.close()

    yield

    # Clean up all data between tests
    cleanup_db = TestingSessionLocal()
    cleanup_db.query(PasswordResetToken).delete()
    cleanup_db.query(User).delete()
    cleanup_db.query(Account).delete()
    cleanup_db.commit()
    cleanup_db.close()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    """Tests the root health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_login_success():
    """Tests successful login and JWT issuance with tenant claims."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rm_test@wealth.bank.com"
    assert data["user"]["role"] == "RM"
    assert data["user"]["account_id"] == "branch_12_central"

def test_login_invalid_password():
    """Tests rejected login when wrong password is provided."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user():
    """Tests rejected login for non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@wealth.bank.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401

def test_get_me_profile():
    """Tests retrieval of authenticated profile via /api/v1/auth/me."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "rm_test@wealth.bank.com"
    assert user_data["account_id"] == "branch_12_central"

def test_protected_route_without_token():
    """Tests that protected route fails with 401 when Authorization header is missing."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_protected_route_invalid_token():
    """Tests that protected route fails with 401 when token is forged or malformed."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401

def test_rbac_compliance_admin_allowed():
    """Tests that ComplianceAdmin can access compliance restricted route."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "comp_test@wealth.bank.com", "password": "AdminPassword123!"},
    )
    admin_token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/compliance/verify-role",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "authorized"

def test_rbac_rm_forbidden():
    """Tests that RM role receives 403 Forbidden when trying to access compliance route."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"},
    )
    rm_token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/compliance/verify-role",
        headers={"Authorization": f"Bearer {rm_token}"},
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_password_reset_flow():
    """Tests complete forgot-password -> reset-password -> login workflow."""
    # 1. Request reset token
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "rm_test@wealth.bank.com"},
    )
    assert forgot_res.status_code == 200
    raw_token = forgot_res.json()["reset_token"]
    assert raw_token is not None

    # 2. Reset password
    new_password = "BrandNewPassword2024!"
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": new_password},
    )
    assert reset_res.status_code == 200
    assert "reset successfully" in reset_res.json()["message"]

    # 3. Verify old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"},
    )
    assert old_login.status_code == 401

    # 4. Verify new password works
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": new_password},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

    # 5. Verify token reuse is prevented
    reuse_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPassword123!"},
    )
    assert reuse_res.status_code == 400

def test_multi_tenant_isolation_scopes():
    """Verifies that different branches receive isolated account scopes in tokens."""
    res_central = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "TestPassword123!"},
    )
    res_north = client.post(
        "/api/v1/auth/login",
        json={"email": "north_rm@wealth.bank.com", "password": "NorthPassword123!"},
    )
    assert res_central.status_code == 200
    assert res_north.status_code == 200

    token_central = res_central.json()["user"]
    token_north = res_north.json()["user"]

    assert token_central["account_id"] == "branch_12_central"
    assert token_north["account_id"] == "branch_01_north"
    assert token_central["account_id"] != token_north["account_id"]
