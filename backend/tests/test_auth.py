import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Tests the root health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_login_success(client: TestClient):
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

def test_login_invalid_password(client: TestClient):
    """Tests rejected login when wrong password is provided."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rm_test@wealth.bank.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    """Tests rejected login for non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@wealth.bank.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401

def test_get_me_profile(client: TestClient):
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

def test_protected_route_without_token(client: TestClient):
    """Tests that protected route fails with 401 when Authorization header is missing."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_protected_route_invalid_token(client: TestClient):
    """Tests that protected route fails with 401 when token is forged or malformed."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401

def test_rbac_compliance_admin_allowed(client: TestClient):
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

def test_rbac_rm_forbidden(client: TestClient):
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

def test_password_reset_flow(client: TestClient):
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

def test_multi_tenant_isolation_scopes(client: TestClient):
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


def test_signup_success(client: TestClient):
    """Verifies that new advisors can successfully register and receive a JWT."""
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Jane Doe",
            "email": "jane.doe@wealth.bank.com",
            "password": "SecurePassword123!",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane.doe@wealth.bank.com"
    assert data["user"]["full_name"] == "Jane Doe"
    assert data["user"]["role"] == "RM"


def test_signup_duplicate_email(client: TestClient):
    """Verifies that registering with an existing email returns 400."""
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Duplicate RM",
            "email": "rm_test@wealth.bank.com",
            "password": "Password123!",
        },
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()

