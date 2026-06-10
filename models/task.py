"""Task ORM model — cleaning task with state machine."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # FK relations
    bin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bin.id"), nullable=False, index=True
    )
    cleaner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # State machine
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending/in_progress/completed/rated"
    )

    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    accept_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    complete_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Completion data (cleaner-filled)
    result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    photos: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Rating data (admin-filled)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    rated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, bin={self.bin_id}, status={self.status})>"