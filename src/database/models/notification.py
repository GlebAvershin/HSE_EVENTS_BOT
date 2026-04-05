"""Модель уведомлений."""
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class Notification(Base):
    """Модель уведомления пользователя."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'new_event', 'friend_going', 'event_reminder'
    title: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    related_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"
