"""Pydantic schemas for Attendance."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttendanceOut(BaseModel):
    id: int
    user_id: int
    clock_in: datetime
    clock_out: Optional[datetime]
    date: date

    model_config = ConfigDict(from_attributes=True)
