"""Модели базы данных."""
from src.database.models.user import User
from src.database.models.event import Event
from src.database.models.friendship import Friendship
from src.database.models.attendance import EventAttendance
from src.database.models.notification import Notification
from src.database.models.user_settings import UserSettings
from src.database.models.event_source import EventSource

__all__ = [
    "User",
    "Event",
    "Friendship",
    "EventAttendance",
    "Notification",
    "UserSettings",
    "EventSource",
]
