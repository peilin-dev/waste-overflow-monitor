"""Pydantic schemas for Block (DTO + VO)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BlockBase(BaseModel):
    """Shared fields used by Create and Out."""
    name: str = Field(..., min_length=1, max_length=50, examples=["Block A"])
    total_floors: int = Field(10, ge=1, le=100)
    bins_per_floor: int = Field(2, ge=1, le=10)


class BlockCreate(BlockBase):
    """POST request body."""
    pass


class BlockUpdate(BaseModel):
    """PATCH request body — all fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    total_floors: Optional[int] = Field(None, ge=1, le=100)
    bins_per_floor: Optional[int] = Field(None, ge=1, le=10)


class BlockOut(BlockBase):
    """Response shape — includes DB-generated fields."""
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)