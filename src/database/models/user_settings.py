"""Модель настроек пользователя."""
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class UserSettings(Base):
    """Модель настроек пользователя."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    notify_new_events: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_friend_going: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_event_reminder: Mapped[bool] = mapped_column(Boolean, default=True)
    hide_attendance: Mapped[bool] = mapped_column(Boolean, default=False)
    hide_from_search: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=["it", "entertainment"]
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id})>"
