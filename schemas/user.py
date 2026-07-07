"""Pydantic schemas for User."""

from datetime import datetime
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    """Shared user fields (without password)."""
    name: str = Field(..., min_length=1, max_length=50, examples=["Alice"])
    username: str = Field(..., min_length=3, max_length=50, examples=["alice01"])
    role: str = Field(..., min_length=1, max_length=50, examples=["cleaner"])
    phone: Optional[str] = Field(None, max_length=20)
    zone: Optional[str] = Field(None, max_length=50)
    shift: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Create payload — includes PLAIN password (server will hash it)."""
    password: str = Field(..., min_length=6, max_length=100, examples=["Init@1234"])


class UserUpdate(BaseModel):
    """Update payload — all fields optional. Password not changed here (separate endpoint)."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    zone: Optional[str] = Field(None, max_length=50)
    shift: Optional[str] = Field(None, max_length=50)
    status: Optional[Literal["active", "inactive"]] = None


class UserPasswordReset(BaseModel):
    """Reset password payload."""
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordChangeRequest(BaseModel):
    """User changes their own password."""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)


class UserPerformance(BaseModel):
    """Cleaner performance metrics."""
    user_id: int
    name: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    average_rating: Optional[float]
    rating_distribution: Dict[str, int]
    on_time_rate: Optional[float]


class UserOut(UserBase):
    """Response — NEVER includes password_hash (security!)."""
    id: int
    status: str
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)