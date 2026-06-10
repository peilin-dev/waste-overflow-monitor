"""Pydantic schemas for User."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    """Shared user fields (without password)."""
    name: str = Field(..., min_length=1, max_length=50, examples=["Alice"])
    account: str = Field(..., min_length=3, max_length=50, examples=["alice01"])
    role: Literal["admin", "cleaner"] = Field(..., examples=["cleaner"])
    phone: Optional[str] = Field(None, max_length=20)
    zone: Optional[str] = Field(None, max_length=50)
    shift: Optional[Literal["morning", "evening", "night"]] = None


class UserCreate(UserBase):
    """Create payload — includes PLAIN password (server will hash it)."""
    password: str = Field(..., min_length=6, max_length=100, examples=["Init@1234"])


class UserUpdate(BaseModel):
    """Update payload — all fields optional. Password not changed here (separate endpoint)."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[Literal["admin", "cleaner"]] = None
    phone: Optional[str] = Field(None, max_length=20)
    zone: Optional[str] = Field(None, max_length=50)
    shift: Optional[Literal["morning", "evening", "night"]] = None
    status: Optional[Literal["active", "inactive"]] = None


class UserPasswordReset(BaseModel):
    """Reset password payload."""
    new_password: str = Field(..., min_length=6, max_length=100)


class UserOut(UserBase):
    """Response — NEVER includes password_hash (security!)."""
    id: int
    status: str
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)