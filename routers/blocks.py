"""
Blocks HTTP endpoints — Controller layer.

Knows HTTP (status codes, paths) but delegates all DB work to crud/block.py.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.user import User
from schemas.block import BlockCreate, BlockUpdate, BlockOut
from crud import blocks as crud_blocks

router = APIRouter(prefix="/api/blocks", tags=["blocks"])


@router.get("", response_model=List[BlockOut], summary="List all blocks")
async def list_blocks(db: AsyncSession = Depends(get_db)):
    return await crud_blocks.get_all(db)


@router.get("/{block_id}", response_model=BlockOut, summary="Get one block by id")
async def get_block(block_id: int, db: AsyncSession = Depends(get_db)):
    block = await crud_blocks.get_by_id(db, block_id)
    if not block:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Block not found")
    return block


@router.post(
    "",
    response_model=BlockOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new block",
)
async def create_block(payload: BlockCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    existing = await crud_blocks.get_by_name(db, payload.name)
    if existing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Block named '{payload.name}' already exists.",
        )
    return await crud_blocks.create(db, payload)


@router.patch("/{block_id}", response_model=BlockOut, summary="Update a block")
async def update_block(
    block_id: int,
    payload: BlockUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    block = await crud_blocks.get_by_id(db, block_id)
    if not block:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Block not found")
    if payload.name is not None and payload.name != block.name:
        if await crud_blocks.get_by_name(db, payload.name):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Block named '{payload.name}' already exists.",
            )
    return await crud_blocks.update(db, block, payload)


@router.delete(
    "/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a block",
)
async def delete_block(block_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    block = await crud_blocks.get_by_id(db, block_id)
    if not block:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Block not found")
    if await crud_blocks.has_bins(db, block_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Cannot delete block while bins still reference it",
        )
    await crud_blocks.delete(db, block)
