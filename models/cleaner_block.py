"""Junction table: cleaner-block M:N assignment."""

from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CleanerBlock(Base):
    __tablename__ = "cleaner_block"

    cleaner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    block_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("block.id", ondelete="CASCADE"),
        primary_key=True, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    def __repr__(self):
        return f"<CleanerBlock(cleaner={self.cleaner_id}, block={self.block_id})>"