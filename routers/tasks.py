"""Tasks HTTP endpoints with state machine and authentication."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin, get_current_admin_or_leader
from datetime import datetime
from schemas.task import TaskCreate, TaskReport, TaskRate, TaskAssign, TaskOut, TaskStats
from crud import tasks as crud_tasks
from crud import bins as crud_bins
from crud import users as crud_users
from models.user import User
from services.task_service import has_open_task_for_bin

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/stats", response_model=TaskStats, summary="Task counts by status")
async def task_stats(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await crud_tasks.get_stats(db)


@router.get("", response_model=List[TaskOut], summary="List tasks (with filters)")
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    cleaner_id: Optional[int] = Query(None),
    bin_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None, description="Inclusive, e.g. 2026-06-01T00:00:00"),
    end_date: Optional[datetime] = Query(None, description="Inclusive, e.g. 2026-06-30T23:59:59"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await crud_tasks.get_all(
        db, status=status_filter, cleaner_id=cleaner_id,
        bin_id=bin_id, start_date=start_date, end_date=end_date,
        skip=skip, limit=limit
    )


@router.get("/{task_id}", response_model=TaskOut, summary="Get one task")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
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

    if await has_open_task_for_bin(db, payload.bin_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Bin {payload.bin_id} already has an open (pending/in_progress) task",
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
    "/{task_id}/assign",
    response_model=TaskOut,
    summary="Admin assigns/reassigns pending task to a cleaner",
)
async def assign_task(
    task_id: int,
    payload: TaskAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_or_leader),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    if task.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot assign: task status is '{task.status}', expected 'pending'",
        )

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
    if cleaner.status != "active":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"User {payload.cleaner_id} is inactive",
        )

    task.cleaner_id = payload.cleaner_id
    await db.commit()
    await db.refresh(task, attribute_names=["bin", "cleaner"])
    return task


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

    # Role check first — return correct 403 before state machine check
    if current_user.role != "cleaner":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only cleaners can accept tasks"
        )

    # State machine check
    if task.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot accept: task status is '{task.status}', expected 'pending'",
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

    if current_user.role != "cleaner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only cleaners can report tasks")

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
    current_admin: User = Depends(get_current_admin_or_leader),
):
    task = await crud_tasks.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    if task.status not in ("completed", "rated"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot rate: task status is '{task.status}', expected 'completed' or 'rated'",
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