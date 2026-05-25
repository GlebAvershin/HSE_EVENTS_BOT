"""Сервис для работы с календарем событий."""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.event import EventRepository


class CalendarService:
    """Сервис для работы с календарем событий."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.session = session
        self.event_repo = EventRepository(session)

    async def get_events_for_week(
        self, category: str | None = None
    ) -> list:
        """
        Получить события на неделю.

        Args:
            category: Категория событий (опционально)

        Returns:
            list: Список событий
        """
        now = datetime.now()
        week_end = now + timedelta(days=7)

        events = await self.event_repo.get_events_by_date_range(
            start_date=now,
            end_date=week_end,
            category=category
        )

        return events

    async def get_events_for_month(
        self, category: str | None = None
    ) -> list:
        """
        Получить события на месяц.

        Args:
            category: Категория событий (опционально)

        Returns:
            list: Список событий
        """
        now = datetime.now()
        month_end = now + timedelta(days=30)

        events = await self.event_repo.get_events_by_date_range(
            start_date=now,
            end_date=month_end,
            category=category
        )

        return events

    async def get_events_for_today(
        self, category: str | None = None
    ) -> list:
        """
        Получить события на сегодня.

        Args:
            category: Категория событий (опционально)

        Returns:
            list: Список событий
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        events = await self.event_repo.get_events_by_date_range(
            start_date=today_start,
            end_date=today_end,
            category=category
        )

        return events

    async def get_events_for_tomorrow(
        self, category: str | None = None
    ) -> list:
        """
        Получить события на завтра.

        Args:
            category: Категория событий (опционально)

        Returns:
            list: Список событий
        """
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        events = await self.event_repo.get_events_by_date_range(
            start_date=tomorrow_start,
            end_date=tomorrow_end,
            category=category
        )

        return events

    def format_calendar_message(
        self, events: list, period: str = "неделю"
    ) -> str:
        """
        Форматировать сообщение календаря.

        Args:
            events: Список событий
            period: Период (неделю, месяц, сегодня, завтра)

        Returns:
            str: Отформатированное сообщение
        """
        if not events:
            return f"😔 На {period} нет запланированных событий."

        text = f"📆 <b>Календарь на {period}</b>\n\n"
        text += f"Найдено событий: {len(events)}\n\n"

        # Группируем события по дням
        events_by_date = {}
        for event in events:
            date_key = event.date_start.strftime("%Y-%m-%d")
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)

        # Форматируем по дням
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        for date_key in sorted(events_by_date.keys()):
            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
            weekday = weekdays[date_obj.weekday()]
            
            if date_obj.date() == today.date():
                date_label = "Сегодня"
            elif date_obj.date() == tomorrow.date():
                date_label = "Завтра"
            else:
                date_label = date_obj.strftime("%d.%m.%Y")
            
            text += f"📅 <b>{date_label} ({weekday})</b>\n"
            
            day_events = events_by_date[date_key]
            for event in day_events:
                time_str = event.date_start.strftime("%H:%M")
                category_emoji = "💻" if event.category == "it" else "🎉"
                
                text += f"{category_emoji} {time_str} - {event.title}\n"
                text += f"   📍 {event.location}\n"
            
            text += "\n"

        return text

    def get_period_name(self, period: str) -> str:
        """
        Получить название периода в правильном падеже.

        Args:
            period: Период (week, month, today, tomorrow)

        Returns:
            str: Название периода
        """
        periods = {
            "week": "неделю",
            "month": "месяц",
            "today": "сегодня",
            "tomorrow": "завтра",
        }
        return periods.get(period, "неделю")
