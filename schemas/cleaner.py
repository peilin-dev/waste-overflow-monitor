"""Schemas for cleaner-block assignment."""

from typing import List
from pydantic import BaseModel, Field


class CleanerBlockAssign(BaseModel):
    """Assign multiple blocks to a cleaner."""
    block_ids: List[int] = Field(..., min_length=1, examples=[[1, 2]])