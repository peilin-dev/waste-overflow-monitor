"""Users HTTP endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin
from core.security import verify_password
from schemas.user import UserCreate, UserUpdate, UserOut, UserPasswordReset, PasswordChangeRequest, UserPerformance
from crud import users as crud_users
from models.task import Task
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


async def _active_admin_count(db: AsyncSession, exclude_id: int) -> int:
    return await db.scalar(
        select(func.count(User.id)).where(
            User.role == "admin",
            User.status == "active",
            User.id != exclude_id,
        )
    ) or 0


@router.get("", response_model=List[UserOut], summary="List users")
async def list_users(
    role: Optional[str] = Query(None, description="Filter: 'admin' or 'cleaner'"),
    status: Optional[str] = Query(None, description="Filter: 'active' or 'inactive', omit for all"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await crud_users.get_all(db, role=role, status=status, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut, summary="Get one user")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    # Check duplicate username
    if await crud_users.get_by_username(db, payload.username):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Username '{payload.username}' already exists.",
        )
    return await crud_users.create(db, payload)


@router.patch("/{user_id}", response_model=UserOut, summary="Update user")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if (
        user.role == "admin"
        and payload.status == "inactive"
        and await _active_admin_count(db, user.id) == 0
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate the last active admin")
    return await crud_users.update(db, user, payload)


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset user password",
)
async def reset_password(
    user_id: int,
    payload: UserPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    await crud_users.update_password(db, user, payload.new_password)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete user (sets status to inactive)",
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.role == "admin" and await _active_admin_count(db, user.id) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate the last active admin")
    await crud_users.soft_delete(db, user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change own password",
)
async def change_password(
    payload: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Old password is incorrect")
    if payload.old_password == payload.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must be different")
    await crud_users.update_password(db, current_user, payload.new_password)


@router.get(
    "/{user_id}/performance",
    response_model=UserPerformance,
    summary="Get cleaner performance metrics",
)
async def user_performance(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    total = await db.scalar(
        select(func.count(Task.id)).where(Task.cleaner_id == user_id)
    )
    completed = await db.scalar(
        select(func.count(Task.id)).where(
            Task.cleaner_id == user_id,
            Task.status.in_(["completed", "rated"]),
        )
    )
    pending = await db.scalar(
        select(func.count(Task.id)).where(
            Task.cleaner_id == user_id,
            Task.status.in_(["pending", "in_progress"]),
        )
    )
    avg_rating = await db.scalar(
        select(func.avg(Task.rating)).where(
            Task.cleaner_id == user_id,
            Task.rating.isnot(None),
        )
    )
    dist_result = await db.execute(
        select(Task.rating, func.count(Task.id))
        .where(Task.cleaner_id == user_id, Task.rating.isnot(None))
        .group_by(Task.rating)
    )
    distribution = {str(i): 0 for i in range(1, 6)}
    for rating, count in dist_result.all():
        distribution[str(rating)] = count

    return {
        "user_id": user.id,
        "name": user.name,
        "total_tasks": total or 0,
        "completed_tasks": completed or 0,
        "pending_tasks": pending or 0,
        "average_rating": float(avg_rating) if avg_rating else None,
        "rating_distribution": distribution,
    }