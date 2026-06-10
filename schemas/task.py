"""Pydantic schemas for Task."""

from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict


TaskResult = Literal["cleaned", "false_alarm", "damaged", "unable"]


class TaskCreate(BaseModel):
    """Admin manually creates a task."""
    bin_id: int = Field(..., ge=1, examples=[1])
    cleaner_id: Optional[int] = Field(
        None, ge=1, description="If null, task is unassigned (any cleaner can accept)"
    )


class TaskReport(BaseModel):
    """Cleaner reports task completion."""
    result: TaskResult = Field(..., examples=["cleaned"])
    photos: Optional[List[str]] = Field(
        None, description="List of photo URLs", examples=[["photo1.jpg", "photo2.jpg"]]
    )


class TaskRate(BaseModel):
    """Admin rates a completed task."""
    rating: int = Field(..., ge=1, le=5, examples=[5])
    comment: Optional[str] = Field(None, max_length=500)


class TaskOut(BaseModel):
    """Task response — all fields."""
    id: int
    bin_id: int
    cleaner_id: Optional[int]
    status: str
    created_at: datetime
    accept_time: Optional[datetime]
    complete_time: Optional[datetime]
    result: Optional[str]
    photos: Optional[List[str]]
    rating: Optional[int]
    comment: Optional[str]
    rated_by: Optional[int]
    rated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """Status counts."""
    total: int
    pending: int
    in_progress: int
    completed: int
    rated: int