"""CRUD for Role + helper to count users per role."""

from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.role import Role
from models.user import User
from schemas.role import RoleCreate, RoleUpdate


async def get_all(db: AsyncSession) -> Sequence[Role]:
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
    return await db.get(Role, role_id)


async def get_by_name(db: AsyncSession, name: str) -> Optional[Role]:
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalars().first()


async def create(db: AsyncSession, payload: RoleCreate) -> Role:
    role = Role(**payload.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def update(db: AsyncSession, role: Role, payload: RoleUpdate) -> Role:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    await db.commit()
    await db.refresh(role)
    return role


async def soft_delete(db: AsyncSession, role: Role) -> Role:
    """Set status='inactive'. Doesn't remove the row."""
    role.status = "inactive"
    await db.commit()
    await db.refresh(role)
    return role


async def restore(db: AsyncSession, role: Role) -> Role:
    """Reactivate an inactive role."""
    role.status = "active"
    await db.commit()
    await db.refresh(role)
    return role


async def count_users_per_role(db: AsyncSession) -> dict:
    """Return {'admin': 2, 'cleaner': 4, ...} from user table (active only)."""
    stmt = (
        select(User.role, func.count(User.id))
        .where(User.status == "active")
        .group_by(User.role)
    )
    result = await db.execute(stmt)
    return dict(result.all())