"""Тесты для EventService."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.services.event_service import EventService
from src.database.models.event import Event


@pytest.fixture
async def session():
    """Создать сессию БД для тестов."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def event_service(session: AsyncSession) -> EventService:
    """Создать экземпляр EventService."""
    return EventService(session)


@pytest.mark.asyncio
async def test_get_events_list(event_service: EventService):
    """Тест получения списка событий с пагинацией."""
    events, total = await event_service.get_events_list(page=1, page_size=5)

    assert isinstance(events, list)
    assert len(events) <= 5
    assert isinstance(total, int)
    assert total >= 0


@pytest.mark.asyncio
async def test_get_events_list_by_category(event_service: EventService):
    """Тест фильтрации событий по категории IT."""
    events, total = await event_service.get_events_list(category="it", page=1, page_size=10)

    assert isinstance(events, list)
    for event in events:
        assert event.category == "it"


@pytest.mark.asyncio
async def test_get_events_list_empty(event_service: EventService):
    """Тест получения пустого списка для несуществующей категории."""
    events, total = await event_service.get_events_list(
        category="nonexistent_category_xyz", page=1, page_size=10
    )

    assert events == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_event_by_id(event_service: EventService, session: AsyncSession):
    """Тест получения события по ID."""
    from sqlalchemy import select

    # Получаем первое существующее событие из БД
    result = await session.execute(select(Event).limit(1))
    existing_event = result.scalar_one_or_none()

    if existing_event:
        event = await event_service.get_event_by_id(existing_event.id)
        assert event is not None
        assert event.id == existing_event.id
        assert event.title == existing_event.title


@pytest.mark.asyncio
async def test_get_event_by_id_not_found(event_service: EventService):
    """Тест получения несуществующего события — возвращает None."""
    event = await event_service.get_event_by_id(999999)
    assert event is None


@pytest.mark.asyncio
async def test_search_events(event_service: EventService):
    """Тест поиска событий по тексту."""
    # Ищем по общему слову, которое скорее всего есть в событиях
    events = await event_service.search_events(search_text="Нижн")

    assert isinstance(events, list)
    # Результаты поиска — все опубликованные
    for event in events:
        assert event.is_published is True


@pytest.mark.asyncio
async def test_get_upcoming_events(event_service: EventService):
    """Тест получения предстоящих событий на N дней."""
    events = await event_service.get_upcoming_events(days=30)

    assert isinstance(events, list)
    # Все события должны быть опубликованы
    for event in events:
        assert event.is_published is True


@pytest.mark.asyncio
async def test_format_event_message(event_service: EventService):
    """Тест форматирования события для Telegram."""
    from datetime import datetime

    # Создаём мок-объект события
    event = Event(
        id=1,
        title="Тестовое событие",
        category="it",
        date_start=datetime(2026, 5, 15, 19, 0),
        location="Нижний Новгород",
        description="Описание тестового события",
        source_url="https://example.com",
        address="ул. Тестовая, 1",
    )

    message = event_service.format_event_message(event, show_full=True)

    assert "Тестовое событие" in message
    assert "💻" in message  # IT emoji
    assert "15.05.2026" in message
    assert "Нижний Новгород" in message
    assert "Описание тестового события" in message
    assert "https://example.com" in message
    assert "ул. Тестовая, 1" in message
