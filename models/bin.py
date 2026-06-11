"""Bin ORM model — maps to MySQL 'bin' table."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Bin(Base):
    __tablename__ = "bin"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="Bin ID"
    )
    block_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("block.id"), nullable=False, index=True,
        comment="Block this bin belongs to"
    )
    floor: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Floor number"
    )
    bin_number: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Position on the floor (1, 2, ...)"
    )
    sensor_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="Hardware sensor ID, e.g. '#1082'"
    )
    current_fill: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="Current fill percentage (0-100)"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        "last_updated", DateTime, nullable=True,
        comment="Last sensor report time"
    )

    def __repr__(self):
        return f"<Bin(id={self.id}, sensor={self.sensor_id}, fill={self.current_fill})>"