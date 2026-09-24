from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_name: str
    branch_code: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    account: Optional[AccountResponse] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None # Provided for development / test verification

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=6)

class ResetPasswordResponse(BaseModel):
    message: str

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)
    account_id: Optional[str] = "branch_12_central"

