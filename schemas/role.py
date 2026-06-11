"""Pydantic schemas for Role."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


AccessLevel = Literal["High", "Medium", "Low"]


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    access_level: AccessLevel = Field("Low")
    permissions_count: int = Field(0, ge=0, le=1000)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    access_level: Optional[AccessLevel] = None
    permissions_count: Optional[int] = Field(None, ge=0, le=1000)
    status: Optional[Literal["active", "inactive"]] = None


class RoleOut(BaseModel):
    """Response with computed assigned_users count."""
    id: int
    name: str
    description: Optional[str]
    access_level: str
    permissions_count: int
    status: str
    assigned_users: int = 0      # 实时从 user 表统计出来
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)