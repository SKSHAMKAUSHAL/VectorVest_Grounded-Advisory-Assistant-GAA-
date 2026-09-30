from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_reset_token,
    hash_reset_token,
)
from app.models.models import User, PasswordResetToken, Account
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest,
)
import uuid
from app.api.deps import get_current_user
from app.core.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=15, window_seconds=60.0, endpoint_tag="auth_login")),
):
    """
    Authenticate a user with email and password.
    Returns a signed JWT bearer token containing user identity and account_id scope.
    """
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact your Compliance Administrator.",
        )

    token_payload = {
        "sub": user.id,
        "email": user.email,
        "account_id": user.account_id,
        "role": user.role,
        "full_name": user.full_name,
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=10, window_seconds=60.0, endpoint_tag="auth_signup")),
):
    """
    Registers a new relationship manager or bank advisor.
    Enforces email uniqueness, creates tenant-scoped user record, and returns signed JWT token.
    """
    clean_email = request.email.lower().strip()
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Ensure target tenant exists
    target_account = request.account_id or "branch_12_central"
    account = db.query(Account).filter(Account.id == target_account).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified branch account does not exist.",
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    new_user = User(
        id=user_id,
        account_id=target_account,
        email=clean_email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name.strip(),
        role="RM",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token_payload = {
        "sub": new_user.id,
        "email": new_user.email,
        "account_id": new_user.account_id,
        "role": new_user.role,
        "full_name": new_user.full_name,
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=5, window_seconds=60.0, endpoint_tag="auth_forgot_password")),
):
    """
    Initiates a password reset flow.
    Generates a cryptographically secure, time-limited token.
    Enforces identical generic response to prevent account enumeration.
    """
    generic_message = "If the email exists in our system, password reset instructions have been dispatched."
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user:
        return ForgotPasswordResponse(
            message=generic_message,
            reset_token=None,
        )

    # Invalidate any prior unused reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).update({"used": True})

    raw_token, token_hash = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False,
    )
    db.add(reset_record)
    db.commit()

    # In production, never leak the raw token in API response
    exposed_token = raw_token if settings.ENVIRONMENT in ("development", "test") else None

    return ForgotPasswordResponse(
        message=generic_message,
        reset_token=exposed_token,
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=10, window_seconds=60.0, endpoint_tag="auth_reset_password")),
):
    """
    Verifies the reset token and updates the user's password.
    """
    token_hash = hash_reset_token(request.token)
    now = datetime.now(timezone.utc)

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == False,
    ).first()

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    # Check expiry (make sure comparison is timezone-aware)
    record_expiry = reset_record.expires_at
    if record_expiry.tzinfo is None:
        record_expiry = record_expiry.replace(tzinfo=timezone.utc)

    if record_expiry < now:
        reset_record.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        )

    # Update user password
    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found.",
        )

    user.password_hash = get_password_hash(request.new_password)
    reset_record.used = True
    db.commit()

    return ResetPasswordResponse(
        message="Password has been reset successfully. You may now log in with your new credentials."
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the authenticated user's profile and account context.
    """
    return UserResponse.model_validate(current_user)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Acknowledge client logout. The client should clear its locally stored JWT bearer token.
    """
    return {"message": f"Successfully logged out user {current_user.email}."}
