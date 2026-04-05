"""Репозиторий для работы с посещениями событий."""
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.attendance import EventAttendance
from src.database.models.user import User


class AttendanceRepository:
    """Репозиторий для работы с посещениями событий."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    async def get_attendance(
        self, user_id: int, event_id: int
    ) -> EventAttendance | None:
        """
        Получить запись о посещении события пользователем.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            EventAttendance | None: Запись о посещении или None
        """
        result = await self.session.execute(
            select(EventAttendance).where(
                and_(
                    EventAttendance.user_id == user_id,
                    EventAttendance.event_id == event_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def set_attendance(
        self, user_id: int, event_id: int, status: str
    ) -> EventAttendance:
        """
        Установить статус посещения события.

        Args:
            user_id: ID пользователя
            event_id: ID события
            status: Статус ('going', 'maybe', 'not_going')

        Returns:
            EventAttendance: Запись о посещении
        """
        attendance = await self.get_attendance(user_id, event_id)

        if attendance:
            # Обновляем существующую запись
            attendance.status = status
        else:
            # Создаем новую запись
            attendance = EventAttendance(
                user_id=user_id, event_id=event_id, status=status
            )
            self.session.add(attendance)

        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance

    async def remove_attendance(self, user_id: int, event_id: int) -> bool:
        """
        Удалить запись о посещении события.

        Args:
            user_id: ID пользователя
            event_id: ID события

        Returns:
            bool: True если успешно удалено
        """
        attendance = await self.get_attendance(user_id, event_id)

        if attendance:
            await self.session.delete(attendance)
            await self.session.commit()
            return True

        return False

    async def get_event_attendees(
        self, event_id: int, status: str | None = None
    ) -> list[User]:
        """
        Получить список пользователей, идущих на событие.

        Args:
            event_id: ID события
            status: Фильтр по статусу (опционально)

        Returns:
            list[User]: Список пользователей
        """
        query = (
            select(User)
            .join(EventAttendance, EventAttendance.user_id == User.id)
            .where(EventAttendance.event_id == event_id)
        )

        if status:
            query = query.where(EventAttendance.status == status)

        result = await self.session.execute(query.order_by(User.first_name))
        return list(result.scalars().all())

    async def get_friends_attending(
        self, event_id: int, user_id: int, status: str | None = None
    ) -> list[User]:
        """
        Получить список друзей пользователя, идущих на событие.

        Args:
            event_id: ID события
            user_id: ID пользователя
            status: Фильтр по статусу (опционально)

        Returns:
            list[User]: Список друзей
        """
        from src.database.models.friendship import Friendship

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
            .where(EventAttendance.event_id == event_id)
        )

        if status:
            query = query.where(EventAttendance.status == status)

        result = await self.session.execute(query.order_by(User.first_name))
        return list(result.scalars().all())

    async def get_attendance_counts(self, event_id: int) -> dict[str, int]:
        """
        Получить количество участников по статусам.

        Args:
            event_id: ID события

        Returns:
            dict: Словарь с количеством по каждому статусу
        """
        result = await self.session.execute(
            select(
                EventAttendance.status, func.count(EventAttendance.id)
            )
            .where(EventAttendance.event_id == event_id)
            .group_by(EventAttendance.status)
        )

        counts = {"going": 0, "maybe": 0, "not_going": 0}
        for status, count in result.all():
            counts[status] = count

        return counts

    async def get_user_events(
        self, user_id: int, status: str | None = None
    ) -> list:
        """
        Получить список событий пользователя.

        Args:
            user_id: ID пользователя
            status: Фильтр по статусу (опционально)

        Returns:
            list: Список событий
        """
        from src.database.models.event import Event

        query = (
            select(Event)
            .join(EventAttendance, EventAttendance.event_id == Event.id)
            .where(EventAttendance.user_id == user_id)
        )

        if status:
            query = query.where(EventAttendance.status == status)

        result = await self.session.execute(query.order_by(Event.date_start))
        return list(result.scalars().all())
