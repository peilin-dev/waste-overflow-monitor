"""Bins HTTP endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, verify_sensor_key
from models.user import User
from schemas.bin import BinCreate, BinUpdate, BinOut, BinFillReport, BinStats
from crud import bins as crud_bins
from crud import blocks as crud_blocks
from crud import tasks as crud_tasks
from services.task_service import maybe_create_overflow_task

router = APIRouter(prefix="/api/bins", tags=["bins"])


@router.get("/stats", response_model=BinStats, summary="Bin counts by status")
async def bin_stats(db: AsyncSession = Depends(get_db)):
    return await crud_bins.get_stats(db)


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
async def create_bin(payload: BinCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
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
    _: User = Depends(get_current_admin),
):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")

    # Check sensor_id uniqueness if it's being changed
    if payload.sensor_id is not None and payload.sensor_id != bin_.sensor_id:
        if await crud_bins.get_by_sensor_id(db, payload.sensor_id):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Sensor ID '{payload.sensor_id}' already exists.",
            )

    # Check position uniqueness if floor or bin_number is being changed
    new_floor = payload.floor if payload.floor is not None else bin_.floor
    new_bin_number = payload.bin_number if payload.bin_number is not None else bin_.bin_number
    if new_floor != bin_.floor or new_bin_number != bin_.bin_number:
        if await crud_bins.get_at_position(db, bin_.block_id, new_floor, new_bin_number):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"A bin already exists at Block {bin_.block_id}, "
                f"Floor {new_floor}, Bin {new_bin_number}.",
            )

    return await crud_bins.update(db, bin_, payload)


@router.delete(
    "/{bin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bin",
)
async def delete_bin(bin_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")
    if await crud_tasks.has_tasks_for_bin(db, bin_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Cannot delete bin while tasks still reference it",
        )
    await crud_bins.delete(db, bin_)


@router.post(
    "/{bin_id}/fill",
    response_model=BinOut,
    summary="Sensor reports fill level",
    description=(
        "Called by hardware sensor to update current fill percentage. "
        "If fill >= 90 and no open task exists, a pending task is auto-created."
    ),
)
async def report_fill(
    bin_id: int,
    payload: BinFillReport,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_sensor_key),
):
    bin_ = await crud_bins.get_by_id(db, bin_id)
    if not bin_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bin not found")

    updated = await crud_bins.update_fill(db, bin_, payload.fill)

    # Auto-task creation if overflow detected
    await maybe_create_overflow_task(db, updated)

    return updated
