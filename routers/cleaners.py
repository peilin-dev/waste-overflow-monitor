"""Cleaner-block assignment endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin, get_current_admin_or_leader
from models.user import User
from schemas.block import BlockOut
from schemas.user import UserOut
from schemas.cleaner import CleanerBlockAssign
from crud import cleaners as crud_cleaners
from crud import users as crud_users
from crud import blocks as crud_blocks

router = APIRouter(prefix="/api", tags=["cleaners"])


@router.get(
    "/cleaners/{cleaner_id}/blocks",
    response_model=List[BlockOut],
    summary="Get blocks assigned to a cleaner",
)
async def list_cleaner_blocks(
    cleaner_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    cleaner = await crud_users.get_by_id(db, cleaner_id)
    if not cleaner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cleaner not found")
    if cleaner.role != "cleaner":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"User {cleaner_id} is not a cleaner (role={cleaner.role})",
        )
    return await crud_cleaners.get_blocks_for_cleaner(db, cleaner_id)


@router.post(
    "/cleaners/{cleaner_id}/blocks",
    response_model=List[BlockOut],
    summary="Assign blocks to a cleaner",
)
async def assign_blocks_to_cleaner(
    cleaner_id: int,
    payload: CleanerBlockAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_or_leader),
):
    # Validate cleaner exists and is a cleaner
    cleaner = await crud_users.get_by_id(db, cleaner_id)
    if not cleaner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cleaner not found")
    if cleaner.role != "cleaner":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"User {cleaner_id} is not a cleaner (role={cleaner.role})",
        )

    # Validate every block exists
    for block_id in payload.block_ids:
        if not await crud_blocks.get_by_id(db, block_id):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Block {block_id} not found"
            )

    return await crud_cleaners.assign_blocks(db, cleaner_id, payload.block_ids)


@router.delete(
    "/cleaners/{cleaner_id}/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a cleaner-block assignment",
)
async def unassign_block_from_cleaner(
    cleaner_id: int,
    block_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_or_leader),
):
    if not await crud_cleaners.unassign_block(db, cleaner_id, block_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")


@router.get(
    "/blocks/{block_id}/cleaners",
    response_model=List[UserOut],
    summary="Get cleaners assigned to a block",
)
async def list_block_cleaners(
    block_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    if not await crud_blocks.get_by_id(db, block_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Block not found")
    return await crud_cleaners.get_cleaners_for_block(db, block_id)