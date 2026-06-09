"""
CRUD operations for Block — Repository layer.

Routers call these functions; this layer knows nothing about HTTP.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.blocks import Block
from schemas.blocks import BlockCreate, BlockUpdate


async def get_all(db: AsyncSession) -> Sequence[Block]:
    result = await db.execute(select(Block).order_by(Block.name))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, block_id: int) -> Optional[Block]:
    return await db.get(Block, block_id)


async def get_by_name(db: AsyncSession, name: str) -> Optional[Block]:
    result = await db.execute(select(Block).where(Block.name == name))
    return result.scalars().first()


async def create(db: AsyncSession, payload: BlockCreate) -> Block:
    block = Block(**payload.model_dump())
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def update(db: AsyncSession, block: Block, payload: BlockUpdate) -> Block:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(block, field, value)
    await db.commit()
    await db.refresh(block)
    return block


async def delete(db: AsyncSession, block: Block) -> None:
    await db.delete(block)
    await db.commit()