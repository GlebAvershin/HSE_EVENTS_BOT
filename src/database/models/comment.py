"""Модель комментария к событию."""
from datetime import datetime

from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class EventComment(Base):
    """Модель комментария к событию."""

    __tablename__ = "event_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="comments")
    event: Mapped["Event"] = relationship("Event", backref="comments")

    def __repr__(self) -> str:
        return f"<EventComment(user_id={self.user_id}, event_id={self.event_id})>"
