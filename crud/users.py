"""CRUD operations for User — Repository layer."""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import hash_password


async def get_all(
    db: AsyncSession,
    role: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[User]:
    """List users with optional filters. Default: all users (no status filter)."""
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if status:
        stmt = stmt.where(User.status == status)
    stmt = stmt.order_by(User.name).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    return await db.get(User, user_id)


async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def create(db: AsyncSession, payload: UserCreate) -> User:
    """Create user with hashed password."""
    data = payload.model_dump()
    plain_password = data.pop("password")  # Remove plain password from dict

    user = User(
        **data,
        password_hash=hash_password(plain_password),  # Hash before storing
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(db: AsyncSession, user: User, new_password: str) -> User:
    user.password_hash = hash_password(new_password)
    await db.commit()
    await db.refresh(user)
    return user


async def soft_delete(db: AsyncSession, user: User) -> User:
    """Soft delete: set status to 'inactive'. Record stays in DB for history."""
    user.status = "inactive"
    await db.commit()
    await db.refresh(user)
    return user