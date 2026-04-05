"""Репозиторий для работы с событиями."""
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.event import Event


class EventRepository:
    """Репозиторий для работы с событиями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    async def get_by_id(self, event_id: int) -> Event | None:
        """
        Получить событие по ID.

        Args:
            event_id: ID события

        Returns:
            Event | None: Событие или None
        """
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_published_events(
        self,
        category: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Event]:
        """
        Получить опубликованные события.

        Args:
            category: Категория событий ('it' или 'entertainment')
            limit: Максимальное количество событий
            offset: Смещение для пагинации

        Returns:
            list[Event]: Список событий
        """
        query = select(Event).where(
            and_(Event.is_published == True, Event.date_start >= datetime.utcnow())
        )

        if category:
            query = query.where(Event.category == category)

        query = query.order_by(Event.date_start).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_events(
        self,
        days: int = 7,
        category: str | None = None,
    ) -> list[Event]:
        """
        Получить предстоящие события на N дней.

        Args:
            days: Количество дней вперед
            category: Категория событий

        Returns:
            list[Event]: Список событий
        """
        from datetime import timedelta

        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        query = select(Event).where(
            and_(
                Event.is_published == True,
                Event.date_start >= now,
                Event.date_start <= end_date,
            )
        )

        if category:
            query = query.where(Event.category == category)

        query = query.order_by(Event.date_start)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_events(
        self,
        search_text: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[Event]:
        """
        Поиск событий по тексту.

        Args:
            search_text: Текст для поиска
            category: Категория событий
            limit: Максимальное количество результатов

        Returns:
            list[Event]: Список найденных событий
        """
        search_pattern = f"%{search_text}%"

        query = select(Event).where(
            and_(
                Event.is_published == True,
                Event.date_start >= datetime.utcnow(),
                or_(
                    Event.title.ilike(search_pattern),
                    Event.description.ilike(search_pattern),
                ),
            )
        )

        if category:
            query = query.where(Event.category == category)

        query = query.order_by(Event.date_start).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        title: str,
        category: str,
        date_start: datetime,
        description: str | None = None,
        date_end: datetime | None = None,
        location: str | None = None,
        address: str | None = None,
        source_url: str | None = None,
        image_url: str | None = None,
        is_published: bool = False,
    ) -> Event:
        """
        Создать новое событие.

        Args:
            title: Название события
            category: Категория ('it' или 'entertainment')
            date_start: Дата начала
            description: Описание
            date_end: Дата окончания
            location: Место проведения
            address: Адрес
            source_url: Ссылка на источник
            image_url: Ссылка на изображение
            is_published: Опубликовано ли событие

        Returns:
            Event: Созданное событие
        """
        event = Event(
            title=title,
            category=category,
            date_start=date_start,
            description=description,
            date_end=date_end,
            location=location,
            address=address,
            source_url=source_url,
            image_url=image_url,
            is_published=is_published,
            is_moderated=False,
        )

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)

        return event

    async def count_published_events(self, category: str | None = None) -> int:
        """
        Подсчитать количество опубликованных событий.

        Args:
            category: Категория событий

        Returns:
            int: Количество событий
        """
        from sqlalchemy import func

        query = select(func.count(Event.id)).where(
            and_(Event.is_published == True, Event.date_start >= datetime.utcnow())
        )

        if category:
            query = query.where(Event.category == category)

        result = await self.session.execute(query)
        return result.scalar() or 0


    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        category: str | None = None,
    ) -> list[Event]:
        """
        Получить события в диапазоне дат.

        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            category: Категория событий

        Returns:
            list[Event]: Список событий
        """
        query = select(Event).where(
            and_(
                Event.is_published == True,
                Event.date_start >= start_date,
                Event.date_start <= end_date,
            )
        )

        if category:
            query = query.where(Event.category == category)

        query = query.order_by(Event.date_start)

        result = await self.session.execute(query)
        return list(result.scalars().all())
