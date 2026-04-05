"""Модель дружеских связей."""
from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class Friendship(Base):
    """Модель дружеских связей между пользователями."""

    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="unique_friendship"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # 'pending', 'accepted', 'rejected'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Friendship(user_id={self.user_id}, friend_id={self.friend_id}, status={self.status})>"
