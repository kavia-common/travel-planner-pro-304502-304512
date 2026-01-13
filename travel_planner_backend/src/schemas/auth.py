from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    full_name: str | None = Field(default=None, description="User's full name")
    created_at: datetime = Field(..., description="User creation timestamp")

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 chars)")
    full_name: str | None = Field(default=None, max_length=200, description="User's full name (optional)")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="Bearer token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserPublic = Field(..., description="Logged-in user")
