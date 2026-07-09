"""Attendance HTTP endpoints — clock-in / clock-out."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin_or_leader
from models.user import User
from schemas.attendance import AttendanceOut
from crud import attendance as crud_attendance

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("/all-today", response_model=List[AttendanceOut])
async def get_all_today(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_or_leader),
):
    return await crud_attendance.get_all_today(db)


@router.get("/today", response_model=Optional[AttendanceOut])
async def get_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await crud_attendance.get_today(db, current_user.id)


@router.post(
    "/clock-in",
    response_model=AttendanceOut,
    status_code=status.HTTP_201_CREATED,
)
async def clock_in(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if await crud_attendance.get_today(db, current_user.id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already clocked in today")
    return await crud_attendance.clock_in(db, current_user.id)


@router.post("/clock-out", response_model=AttendanceOut)
async def clock_out(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await crud_attendance.get_today(db, current_user.id)
    if not record:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No clock-in record for today")
    if record.clock_out:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already clocked out today")
    return await crud_attendance.clock_out(db, record)
