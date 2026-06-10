"""Tasks HTTP endpoints with state machine and authentication."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin
from schemas.task import TaskCreate, TaskReport, TaskRate, TaskOut, TaskStats
from crud import tasks as crud_tasks
from crud import bins as crud_bins
from crud import users as crud_users
from models.user import User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/stats", response_model=TaskStats, summary="Task counts by status")
async def task_stats(db: AsyncSession = Depends(get_db)):
    return await crud_tasks.get_stats(db)


@router.get("", response_model=List[TaskOut], summary="List tasks (with filters)")
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    cleaner_id: Optional[int] = Query(None),
    bin_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await crud_tasks.get_all(
        db, status=status_filter, cleaner_id=cleaner_id,
        bin_id=bin_id, skip=skip, limit=limit
    )


@router.get("/{task_id}", response_model=TaskOut, summary="Get one task")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.post(
    "",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task (admin)",
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),  # admin only
):
    if not await crud_bins.get_by_id(db, payload.bin_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Bin {payload.bin_id} not found"
        )

    if payload.cleaner_id is not None:
        cleaner = await crud_users.get_by_id(db, payload.cleaner_id)
        if not cleaner:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"User {payload.cleaner_id} not found"
            )
        if cleaner.role != "cleaner":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"User {payload.cleaner_id} is not a cleaner",
            )

    return await crud_tasks.create(db, payload)


@router.post(
    "/{task_id}/accept",
    response_model=TaskOut,
    summary="Cleaner accepts task (pending → in_progress)",
)
async def accept_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    # State machine check
    if task.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot accept: task status is '{task.status}', expected 'pending'",
        )

    if current_user.role != "cleaner":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only cleaners can accept tasks"
        )

    # If pre-assigned, must be the same cleaner
    if task.cleaner_id is not None and task.cleaner_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This task is assigned to another cleaner",
        )

    return await crud_tasks.accept(db, task, current_user.id)


@router.post(
    "/{task_id}/report",
    response_model=TaskOut,
    summary="Cleaner reports completion (in_progress → completed)",
)
async def report_task(
    task_id: int,
    payload: TaskReport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    if task.status != "in_progress":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot report: task status is '{task.status}', expected 'in_progress'",
        )

    if task.cleaner_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the assigned cleaner can report this task",
        )

    return await crud_tasks.report(db, task, payload)


@router.post(
    "/{task_id}/rate",
    response_model=TaskOut,
    summary="Admin rates task (completed → rated)",
)
async def rate_task(
    task_id: int,
    payload: TaskRate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    if task.status != "completed":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot rate: task status is '{task.status}', expected 'completed'",
        )

    return await crud_tasks.rate(db, task, payload, current_admin.id)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task (admin)",
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    await crud_tasks.delete(db, task)