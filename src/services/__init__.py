"""Сервисы бизнес-логики."""
from src.services.event_service import EventService
from src.services.friendship_service import FriendshipService
from src.services.attendance_service import AttendanceService
from src.services.calendar_service import CalendarService
from src.services.notification_service import NotificationService

__all__ = [
    "EventService",
    "FriendshipService",
    "AttendanceService",
    "CalendarService",
    "NotificationService",
]
