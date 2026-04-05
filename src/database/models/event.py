"""Модель события."""
from datetime import datetime

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class Event(Base):
    """Модель события/мероприятия."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'it' или 'entertainment'
    date_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    date_end: Mapped[datetime | None] = mapped_column(DateTime)
    location: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    attendances: Mapped[list["EventAttendance"]] = relationship(
        "EventAttendance", back_populates="event"
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, category={self.category})>"
