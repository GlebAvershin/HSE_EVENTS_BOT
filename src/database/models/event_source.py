"""Модель источника событий."""
from datetime import datetime

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class EventSource(Base):
    """Модель источника событий для парсинга."""

    __tablename__ = "event_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    parser_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'yandex_afisha', 'vk', 'custom'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_parsed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EventSource(id={self.id}, name={self.name}, parser_type={self.parser_type})>"
