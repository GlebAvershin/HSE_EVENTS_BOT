"""Модель посещения событий."""
from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class EventAttendance(Base):
    """Модель посещения события пользователем."""

    __tablename__ = "event_attendances"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="unique_attendance"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="going"
    )  # 'going', 'maybe', 'not_going'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="attendances")
    event: Mapped["Event"] = relationship("Event", back_populates="attendances")

    def __repr__(self) -> str:
        return f"<EventAttendance(user_id={self.user_id}, event_id={self.event_id}, status={self.status})>"
