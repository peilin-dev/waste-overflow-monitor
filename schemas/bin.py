"""Pydantic schemas for Bin (DTO + VO)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field


def _calculate_status(fill: int) -> str:
    """Derive status color from fill percentage."""
    if fill >= 90:
        return "full"       # red
    elif fill >= 60:
        return "warning"    # yellow
    return "normal"         # green


class BinBase(BaseModel):
    """Shared fields used by Create and Out."""
    block_id: int = Field(..., ge=1, examples=[1])
    floor: int = Field(..., ge=1, le=100, examples=[5])
    bin_number: int = Field(..., ge=1, le=10, examples=[1])
    sensor_id: str = Field(..., min_length=1, max_length=20, examples=["#1051"])


class BinCreate(BinBase):
    """POST request body."""
    pass


class BinUpdate(BaseModel):
    """PATCH request body — all fields optional."""
    floor: Optional[int] = Field(None, ge=1, le=100)
    bin_number: Optional[int] = Field(None, ge=1, le=10)
    sensor_id: Optional[str] = Field(None, min_length=1, max_length=20)


class BinFillReport(BaseModel):
    """Sensor report payload — just the fill value."""
    fill: int = Field(..., ge=0, le=100, examples=[75])


class BinStats(BaseModel):
    """Bin counts by computed status."""
    total: int
    normal: int    # fill < 60
    warning: int   # 60 <= fill < 90
    full: int      # fill >= 90


class BinOut(BinBase):
    """Response shape — includes DB fields + computed status."""
    id: int
    current_fill: int
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def status(self) -> str:
        """Derived from current_fill: normal / warning / full."""
        return _calculate_status(self.current_fill)