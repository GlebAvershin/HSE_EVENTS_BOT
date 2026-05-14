"""Модель отзыва на событие."""
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class EventReview(Base):
    """Модель отзыва/оценки события пользователем."""

    __tablename__ = "event_reviews"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="unique_review"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="reviews")
    event: Mapped["Event"] = relationship("Event", backref="reviews")

    def __repr__(self) -> str:
        return f"<EventReview(user_id={self.user_id}, event_id={self.event_id}, rating={self.rating})>"
