"""Сервис для работы с событиями."""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.event import EventRepository
from src.database.models.event import Event


class EventService:
    """Сервис для работы с событиями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.event_repo = EventRepository(session)

    async def get_event_by_id(self, event_id: int) -> Event | None:
        """
        Получить событие по ID.

        Args:
            event_id: ID события

        Returns:
            Event | None: Событие или None
        """
        return await self.event_repo.get_by_id(event_id)

    async def get_events_list(
        self,
        category: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Event], int]:
        """
        Получить список событий с пагинацией.

        Args:
            category: Категория событий
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы

        Returns:
            tuple[list[Event], int]: Список событий и общее количество
        """
        offset = (page - 1) * page_size
        events = await self.event_repo.get_published_events(
            category=category, limit=page_size, offset=offset
        )
        total = await self.event_repo.count_published_events(category=category)

        return events, total

    async def get_upcoming_events(
        self, days: int = 7, category: str | None = None
    ) -> list[Event]:
        """
        Получить предстоящие события.

        Args:
            days: Количество дней вперед
            category: Категория событий

        Returns:
            list[Event]: Список событий
        """
        return await self.event_repo.get_upcoming_events(days=days, category=category)

    async def search_events(
        self, search_text: str, category: str | None = None
    ) -> list[Event]:
        """
        Поиск событий.

        Args:
            search_text: Текст для поиска
            category: Категория событий

        Returns:
            list[Event]: Список найденных событий
        """
        return await self.event_repo.search_events(
            search_text=search_text, category=category
        )

    def format_event_message(self, event: Event, show_full: bool = False) -> str:
        """
        Форматировать событие для отображения в боте.

        Args:
            event: Событие
            show_full: Показать полное описание

        Returns:
            str: Отформатированное сообщение
        """
        # Эмодзи для категорий
        category_emoji = {"it": "💻", "entertainment": "🎉"}
        emoji = category_emoji.get(event.category, "📅")

        # Форматирование даты
        date_str = event.date_start.strftime("%d.%m.%Y %H:%M")

        # Базовая информация
        message = f"{emoji} <b>{event.title}</b>\n\n"
        message += f"📅 {date_str}\n"

        if event.location:
            message += f"📍 {event.location}\n"

        if show_full and event.description:
            # Ограничиваем длину описания
            description = event.description[:500]
            if len(event.description) > 500:
                description += "..."
            message += f"\n{description}\n"

        if event.address:
            message += f"\n🗺 {event.address}\n"

        if event.source_url:
            message += f"\n🔗 <a href='{event.source_url}'>Подробнее</a>"

        return message

    def get_category_name(self, category: str) -> str:
        """
        Получить название категории на русском.

        Args:
            category: Код категории

        Returns:
            str: Название категории
        """
        categories = {"it": "IT-мероприятия", "entertainment": "Развлечения"}
        return categories.get(category, "Все события")
