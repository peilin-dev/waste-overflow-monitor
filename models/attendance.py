"""Attendance ORM model — maps to MySQL 'attendance' table."""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import Integer, ForeignKey, DateTime, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_attendance_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, index=True
    )
    clock_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
