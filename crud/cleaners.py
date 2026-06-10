"""CRUD for cleaner-block assignments."""

from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.cleaner_block import CleanerBlock
from models.block import Block
from models.user import User


async def get_blocks_for_cleaner(
    db: AsyncSession, cleaner_id: int
) -> Sequence[Block]:
    """All blocks assigned to a cleaner."""
    stmt = (
        select(Block)
        .join(CleanerBlock, Block.id == CleanerBlock.block_id)
        .where(CleanerBlock.cleaner_id == cleaner_id)
        .order_by(Block.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_cleaners_for_block(
    db: AsyncSession, block_id: int
) -> Sequence[User]:
    """All cleaners assigned to a block (active only)."""
    stmt = (
        select(User)
        .join(CleanerBlock, User.id == CleanerBlock.cleaner_id)
        .where(CleanerBlock.block_id == block_id)
        .where(User.status == "active")
        .order_by(User.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def assign_blocks(
    db: AsyncSession, cleaner_id: int, block_ids: list[int]
) -> Sequence[Block]:
    """Add new assignments. Idempotent — skips duplicates."""
    # Find existing assignments to avoid PK duplicates
    existing_stmt = select(CleanerBlock.block_id).where(
        CleanerBlock.cleaner_id == cleaner_id,
        CleanerBlock.block_id.in_(block_ids),
    )
    result = await db.execute(existing_stmt)
    existing_ids = set(result.scalars().all())

    # Only insert new ones
    for block_id in block_ids:
        if block_id not in existing_ids:
            db.add(CleanerBlock(cleaner_id=cleaner_id, block_id=block_id))

    await db.commit()
    return await get_blocks_for_cleaner(db, cleaner_id)


async def unassign_block(
    db: AsyncSession, cleaner_id: int, block_id: int
) -> bool:
    """Delete one assignment. Returns True if it existed."""
    stmt = delete(CleanerBlock).where(
        CleanerBlock.cleaner_id == cleaner_id,
        CleanerBlock.block_id == block_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0