"""Репозитории для работы с БД."""
from src.database.repositories.user import UserRepository
from src.database.repositories.event import EventRepository
from src.database.repositories.friendship import FriendshipRepository
from src.database.repositories.attendance import AttendanceRepository

__all__ = ["UserRepository", "EventRepository", "FriendshipRepository", "AttendanceRepository"]
