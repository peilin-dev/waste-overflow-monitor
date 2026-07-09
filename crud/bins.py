"""CRUD operations for Bin — Repository layer."""

from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.bin import Bin
from schemas.bin import BinCreate, BinUpdate
from utils.time import now_myt


async def get_all(
    db: AsyncSession,
    block_id: Optional[int] = None,
    min_fill: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Bin]:
    """List bins with optional filters."""
    stmt = select(Bin)

    if block_id is not None:
        stmt = stmt.where(Bin.block_id == block_id)
    if min_fill is not None:
        stmt = stmt.where(Bin.current_fill >= min_fill)

    stmt = (
        stmt.order_by(Bin.block_id, Bin.floor, Bin.bin_number)
            .offset(skip)
            .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_id(db: AsyncSession, bin_id: int) -> Optional[Bin]:
    return await db.get(Bin, bin_id)


async def get_by_sensor_id(db: AsyncSession, sensor_id: str) -> Optional[Bin]:
    result = await db.execute(select(Bin).where(Bin.sensor_id == sensor_id))
    return result.scalars().first()


async def get_at_position(
    db: AsyncSession, block_id: int, floor: int, bin_number: int
) -> Optional[Bin]:
    """Check if a bin already exists at the given position."""
    result = await db.execute(
        select(Bin).where(
            Bin.block_id == block_id,
            Bin.floor == floor,
            Bin.bin_number == bin_number,
        )
    )
    return result.scalars().first()


async def create(db: AsyncSession, payload: BinCreate) -> Bin:
    bin_ = Bin(**payload.model_dump())
    db.add(bin_)
    await db.commit()
    await db.refresh(bin_)
    return bin_


async def update(db: AsyncSession, bin_: Bin, payload: BinUpdate) -> Bin:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(bin_, field, value)
    await db.commit()
    await db.refresh(bin_)
    return bin_


async def update_fill(db: AsyncSession, bin_: Bin, fill: int) -> Bin:
    """Update fill level from sensor report."""
    bin_.current_fill = fill
    bin_.updated_at = now_myt()
    await db.commit()
    await db.refresh(bin_)
    return bin_


async def delete(db: AsyncSession, bin_: Bin) -> None:
    await db.delete(bin_)
    await db.commit()


async def get_stats(db: AsyncSession) -> dict:
    """Count bins by derived status (normal/warning/full)."""
    result = await db.execute(select(Bin.current_fill))
    fills = list(result.scalars().all())
    return {
        "total": len(fills),
        "normal": sum(1 for f in fills if f < 60),
        "warning": sum(1 for f in fills if 60 <= f < 90),
        "full": sum(1 for f in fills if f >= 90),
    }