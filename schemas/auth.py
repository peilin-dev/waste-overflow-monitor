"""Schemas for authentication endpoints."""

from pydantic import BaseModel, Field
from schemas.user import UserOut


class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["admin123"])


class TokenResponse(BaseModel):
    """Login successful response — token + user info."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)