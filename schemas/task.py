"""Pydantic schemas for Task."""

from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict


TaskResult = Literal["cleaned", "false_alarm", "damaged", "unable"]


class TaskBinInfo(BaseModel):
    """Embedded bin info inside task response."""
    id: int
    block_id: int
    floor: int
    bin_number: int
    sensor_id: str
    current_fill: int

    model_config = ConfigDict(from_attributes=True)


class TaskCleanerInfo(BaseModel):
    """Embedded cleaner info inside task response."""
    id: int
    name: str
    username: str
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


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


class TaskAssign(BaseModel):
    """Admin assigns a pending task to a cleaner."""
    cleaner_id: int = Field(..., ge=1, examples=[1001])


class TaskOut(BaseModel):
    """Task response — all fields with embedded bin and cleaner info."""
    id: int
    bin_id: int
    cleaner_id: Optional[int]
    status: str
    created_at: datetime
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[str]
    photos: Optional[List[str]]
    rating: Optional[int]
    comment: Optional[str]
    rated_by: Optional[int]
    rated_at: Optional[datetime]
    bin: Optional[TaskBinInfo] = None
    cleaner: Optional[TaskCleanerInfo] = None

    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """Status counts."""
    total: int
    pending: int
    in_progress: int
    completed: int
    rated: int