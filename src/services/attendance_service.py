"""Сервис для работы с посещениями событий."""
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.attendance import AttendanceRepository
from src.database.repositories.event import EventRepository
from src.database.models.user import User


class AttendanceService:
    """Сервис для работы с посещениями событий."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.session = session
        self.attendance_repo = AttendanceRepository(session)
        self.event_repo = EventRepository(session)

    async def set_going(self, user_id: int, event_id: int) -> tuple[bool, str]:
        """
        Отметить "Я пойду" на событие.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        # Проверяем что событие существует
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            return False, "❌ Событие не найдено"

        # Устанавливаем статус
        await self.attendance_repo.set_attendance(user_id, event_id, "going")

        return True, "✅ Вы отметили, что пойдете на это событие!"

    async def set_maybe(self, user_id: int, event_id: int) -> tuple[bool, str]:
        """
        Отметить "Возможно" на событие.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        # Проверяем что событие существует
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            return False, "❌ Событие не найдено"

        # Устанавливаем статус
        await self.attendance_repo.set_attendance(user_id, event_id, "maybe")

        return True, "❓ Вы отметили, что возможно пойдете на это событие"

    async def remove_attendance(
        self, user_id: int, event_id: int
    ) -> tuple[bool, str]:
        """
        Удалить отметку о посещении.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        success = await self.attendance_repo.remove_attendance(user_id, event_id)

        if success:
            return True, "🗑 Отметка удалена"
        else:
            return False, "❌ Отметка не найдена"

    async def get_user_status(
        self, user_id: int, event_id: int
    ) -> str | None:
        """
        Получить статус пользователя для события.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            str | None: Статус или None
        """
        attendance = await self.attendance_repo.get_attendance(user_id, event_id)
        return attendance.status if attendance else None

    async def get_event_stats(self, event_id: int) -> dict:
        """
        Получить статистику посещений события.

        Args:
            event_id: ID события

        Returns:
            dict: Статистика
        """
        counts = await self.attendance_repo.get_attendance_counts(event_id)
        total = counts["going"] + counts["maybe"]

        return {
            "going": counts["going"],
            "maybe": counts["maybe"],
            "total": total,
        }

    async def get_friends_going(
        self, event_id: int, user_id: int
    ) -> list[User]:
        """
        Получить список друзей, идущих на событие.
        Исключает пользователей, скрывших свои посещения.

        Args:
            event_id: ID события
            user_id: ID пользователя

        Returns:
            list[User]: Список друзей
        """
        from sqlalchemy import select, and_
        from src.database.models.attendance import EventAttendance
        from src.database.models.friendship import Friendship
        from src.database.models.user_settings import UserSettings

        query = (
            select(User)
            .join(EventAttendance, EventAttendance.user_id == User.id)
            .join(
                Friendship,
                and_(
                    Friendship.friend_id == User.id,
                    Friendship.user_id == user_id,
                    Friendship.status == "accepted",
                ),
            )
            .outerjoin(UserSettings, UserSettings.user_id == User.id)
            .where(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.status == "going",
                    (UserSettings.hide_attendance == False) | (UserSettings.hide_attendance.is_(None)),
                )
            )
            .order_by(User.first_name)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_friends_maybe(
        self, event_id: int, user_id: int
    ) -> list[User]:
        """
        Получить список друзей, которые возможно пойдут.
        Исключает пользователей, скрывших свои посещения.

        Args:
            event_id: ID события
            user_id: ID пользователя

        Returns:
            list[User]: Список друзей
        """
        from sqlalchemy import select, and_
        from src.database.models.attendance import EventAttendance
        from src.database.models.friendship import Friendship
        from src.database.models.user_settings import UserSettings

        query = (
            select(User)
            .join(EventAttendance, EventAttendance.user_id == User.id)
            .join(
                Friendship,
                and_(
                    Friendship.friend_id == User.id,
                    Friendship.user_id == user_id,
                    Friendship.status == "accepted",
                ),
            )
            .outerjoin(UserSettings, UserSettings.user_id == User.id)
            .where(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.status == "maybe",
                    (UserSettings.hide_attendance == False) | (UserSettings.hide_attendance.is_(None)),
                )
            )
            .order_by(User.first_name)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    def format_friends_list(self, friends: list[User]) -> str:
        """
        Форматировать список друзей для отображения.

        Args:
            friends: Список друзей

        Returns:
            str: Отформатированный список
        """
        if not friends:
            return "Никого из ваших друзей"

        lines = []
        for friend in friends:
            name = friend.first_name or friend.username or "Пользователь"
            if friend.username:
                lines.append(f"• {name} (@{friend.username})")
            else:
                lines.append(f"• {name}")

        return "\n".join(lines)
