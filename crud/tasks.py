"""CRUD for Task with state transitions."""

from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task
from schemas.task import TaskCreate, TaskReport, TaskRate
from utils.time import now_myt


def _with_relations(stmt):
    """Apply eager-load options for bin and cleaner."""
    return stmt.options(selectinload(Task.bin), selectinload(Task.cleaner))


async def get_all(
    db: AsyncSession,
    status: Optional[str] = None,
    cleaner_id: Optional[int] = None,
    bin_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 500,
) -> Sequence[Task]:
    stmt = _with_relations(select(Task))
    if status:
        stmt = stmt.where(Task.status == status)
    if cleaner_id is not None:
        stmt = stmt.where(Task.cleaner_id == cleaner_id)
    if bin_id is not None:
        stmt = stmt.where(Task.bin_id == bin_id)
    if start_date:
        stmt = stmt.where(Task.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Task.created_at <= end_date)
    stmt = stmt.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
    stmt = _with_relations(select(Task)).where(Task.id == task_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def has_tasks_for_bin(db: AsyncSession, bin_id: int) -> bool:
    result = await db.execute(
        select(Task.id).where(
            Task.bin_id == bin_id,
            Task.status.in_(["pending", "in_progress"]),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def create(db: AsyncSession, payload: TaskCreate) -> Task:
    task = Task(
        bin_id=payload.bin_id,
        cleaner_id=payload.cleaner_id,
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task, attribute_names=["bin", "cleaner"])
    return task


async def accept(db: AsyncSession, task: Task, cleaner_id: int) -> Task:
    """State transition: pending → in_progress."""
    task.cleaner_id = cleaner_id
    task.status = "in_progress"
    task.accepted_at = now_myt()
    await db.commit()
    await db.refresh(task, attribute_names=["bin", "cleaner"])
    return task


async def report(db: AsyncSession, task: Task, payload: TaskReport) -> Task:
    """State transition: in_progress → completed."""
    task.status = "completed"
    task.completed_at = now_myt()
    task.result = payload.result
    task.photos = payload.photos
    await db.commit()
    await db.refresh(task, attribute_names=["bin", "cleaner"])
    return task


async def rate(db: AsyncSession, task: Task, payload: TaskRate, admin_id: int) -> Task:
    """State transition: completed → rated (or re-rate an already rated task)."""
    if task.status == "completed":
        task.status = "rated"
    task.rating = payload.rating
    task.comment = payload.comment
    task.rated_by = admin_id
    task.rated_at = now_myt()
    await db.commit()
    await db.refresh(task, attribute_names=["bin", "cleaner"])
    return task


async def delete(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()


async def get_stats(db: AsyncSession) -> dict:
    """Count tasks grouped by status."""
    stmt = select(Task.status, func.count(Task.id)).group_by(Task.status)
    result = await db.execute(stmt)
    counts = dict(result.all())
    return {
        "total": sum(counts.values()),
        "pending": counts.get("pending", 0),
        "in_progress": counts.get("in_progress", 0),
        "completed": counts.get("completed", 0),
        "rated": counts.get("rated", 0),
    }
