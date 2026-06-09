
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


# Async engine (connection pool)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,    # Log SQL when DEBUG=true
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base for all ORM models (SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass


# FastAPI dependency — one AsyncSession per request
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise