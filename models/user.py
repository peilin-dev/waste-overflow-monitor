"""User ORM model — maps to MySQL 'user' table."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Display name"
    )
    account: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="Login account"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="bcrypt hashed password — never returned"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="'admin' or 'cleaner'"
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False,
        comment="'active' or 'inactive' (soft delete)"
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    def __repr__(self):
        return f"<User(id={self.id}, account={self.account}, role={self.role})>"