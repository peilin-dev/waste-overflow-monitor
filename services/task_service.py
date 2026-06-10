"""
Cross-module service logic.

Coordinates between Bin and Task — when a bin overflows,
automatically create a pending task for cleaners to pick up.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bin import Bin
from models.task import Task
from schemas.task import TaskCreate
from crud import tasks as crud_tasks


# Auto-create a task when bin fill reaches this percentage
OVERFLOW_THRESHOLD = 90


async def has_open_task_for_bin(db: AsyncSession, bin_id: int) -> bool:
    """Check if there's an active (pending / in_progress) task for this bin."""
    stmt = select(Task).where(
        Task.bin_id == bin_id,
        Task.status.in_(["pending", "in_progress"]),
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None


async def maybe_create_overflow_task(
    db: AsyncSession, bin_: Bin
) -> Optional[Task]:
    """
    Auto-create a pending task if both:
      1. bin.current_fill >= OVERFLOW_THRESHOLD
      2. No open (pending / in_progress) task already exists for this bin

    Returns the new task, or None if nothing was created.
    """
    if bin_.current_fill < OVERFLOW_THRESHOLD:
        return None

    if await has_open_task_for_bin(db, bin_.id):
        return None  # avoid duplicates

    payload = TaskCreate(bin_id=bin_.id, cleaner_id=None)  # unassigned
    return await crud_tasks.create(db, payload)