"""Модель пользователя."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class User(Base):
    """Модель пользователя Telegram."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", back_populates="user", uselist=False
    )
    attendances: Mapped[list["EventAttendance"]] = relationship(
        "EventAttendance", back_populates="user"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
