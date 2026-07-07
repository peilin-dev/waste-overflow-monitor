"""CRUD for Attendance — clock-in/out logic."""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.attendance import Attendance


async def get_today(db: AsyncSession, user_id: int) -> Optional[Attendance]:
    result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.date == date.today(),
        )
    )
    return result.scalars().first()


async def clock_in(db: AsyncSession, user_id: int) -> Attendance:
    record = Attendance(
        user_id=user_id,
        clock_in=datetime.now(),
        date=date.today(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def clock_out(db: AsyncSession, record: Attendance) -> Attendance:
    record.clock_out = datetime.now()
    await db.commit()
    await db.refresh(record)
    return record
