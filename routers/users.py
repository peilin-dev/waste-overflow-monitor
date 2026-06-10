"""Users HTTP endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.user import UserCreate, UserUpdate, UserOut, UserPasswordReset
from crud import users as crud_users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut], summary="List users")
async def list_users(
    role: Optional[str] = Query(None, description="Filter: 'admin' or 'cleaner'"),
    status: str = Query("active", description="Filter: 'active' (default) or 'inactive'"),
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
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate account
    if await crud_users.get_by_account(db, payload.account):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Account '{payload.account}' already exists.",
        )
    return await crud_users.create(db, payload)


@router.patch("/{user_id}", response_model=UserOut, summary="Update user")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
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
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    await crud_users.soft_delete(db, user)