"""CRUD for Attendance — clock-in/out logic."""

from datetime import date, datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.attendance import Attendance

_MYT = timezone(timedelta(hours=8))


def _now() -> datetime:
    """Current time in Malaysia Time (UTC+8), stored as naive datetime."""
    return datetime.now(_MYT).replace(tzinfo=None)


async def get_today(db: AsyncSession, user_id: int) -> Optional[Attendance]:
    result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.date == _now().date(),
        )
    )
    return result.scalars().first()


async def clock_in(db: AsyncSession, user_id: int) -> Attendance:
    now = _now()
    record = Attendance(
        user_id=user_id,
        clock_in=now,
        date=now.date(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def clock_out(db: AsyncSession, record: Attendance) -> Attendance:
    record.clock_out = _now()
    await db.commit()
    await db.refresh(record)
    return record
