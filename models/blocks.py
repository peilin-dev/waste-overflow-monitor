"""Block ORM model — maps to MySQL 'block' table."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Block(Base):
    __tablename__ = "block"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="Block ID"
    )
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="Block name, e.g. 'Block A'"
    )
    total_floors: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False,
        comment="Number of floors"
    )
    bins_per_floor: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False,
        comment="Bins per floor (1-10)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False,
        comment="Creation timestamp"
    )

    def __repr__(self):
        return f"<Block(id={self.id}, name={self.name})>"