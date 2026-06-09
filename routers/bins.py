"""Bins HTTP endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.bin import BinCreate, BinUpdate, BinOut, BinFillReport
from crud import bins as crud_bins
from crud import blocks as crud_blocks

router = APIRouter(prefix="/api/bins", tags=["bins"])


@router.get(
    "",
    response_model=List[BinOut],
    summary="List bins (with optional filters)",
)
async def list_bins(
    block_id: Optional[int] = Query(None, description="Filter by block"),
    min_fill: Optional[int] = Query(None, ge=0, le=100, description="Filter bins with fill >= this"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await crud_bins.get_all(db, block_id=block_id, min_fill=min_fill, skip=skip, limit=limit)


@router.get("/{bin_id}", response_model=BinOut, summary="Get one bin")
async def get_bin(bin_id: int, db: AsyncSession = Depends(get_db)):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")
    return bin_


@router.post(
    "",
    response_model=BinOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bin",
)
async def create_bin(payload: BinCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verify block exists
    block = await crud_blocks.get_by_id(db, payload.block_id)
    if not block:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Block {payload.block_id} not found",
        )

    # 2. Check duplicate sensor_id
    if await crud_bins.get_by_sensor_id(db, payload.sensor_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Sensor ID '{payload.sensor_id}' already exists.",
        )

    # 3. Check duplicate position (same block + floor + bin_number)
    if await crud_bins.get_at_position(
        db, payload.block_id, payload.floor, payload.bin_number
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"A bin already exists at Block {payload.block_id}, "
            f"Floor {payload.floor}, Bin {payload.bin_number}.",
        )

    return await crud_bins.create(db, payload)


@router.patch("/{bin_id}", response_model=BinOut, summary="Update a bin")
async def update_bin(
    bin_id: int,
    payload: BinUpdate,
    db: AsyncSession = Depends(get_db),
):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")
    return await crud_bins.update(db, bin_, payload)


@router.delete(
    "/{bin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bin",
)
async def delete_bin(bin_id: int, db: AsyncSession = Depends(get_db)):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")
    await crud_bins.delete(db, bin_)


@router.post(
    "/{bin_id}/fill",
    response_model=BinOut,
    summary="Sensor reports fill level",
    description=(
        "Called by hardware sensor to update current fill percentage. "
        "TODO: when fill >= 90, auto-create a pending task (after Task module is built)."
    ),
)
async def report_fill(
    bin_id: int,
    payload: BinFillReport,
    db: AsyncSession = Depends(get_db),
):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")

    updated = await crud_bins.update_fill(db, bin_, payload.fill)

    # TODO: 等 Task 模块写完后,在这里加自动派单逻辑:
    # if updated.current_fill >= 90 and not has_active_task(db, bin_id):
    #     await crud_tasks.create_from_overflow(db, updated)

    return updated