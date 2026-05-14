"""Тесты для AttendanceService."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.services.attendance_service import AttendanceService
from src.database.models.event import Event
from src.database.models.user import User
from src.database.models.attendance import EventAttendance


@pytest.fixture
async def session():
    """Создать сессию БД для тестов."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def attendance_service(session: AsyncSession) -> AttendanceService:
    """Создать экземпляр AttendanceService."""
    return AttendanceService(session)


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Получить или создать тестового пользователя."""
    result = await session.execute(
        select(User).where(User.telegram_id == 999999999)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=999999999,
            username="test_attendance_user",
            first_name="Test",
            last_name="User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


@pytest.fixture
async def test_event(session: AsyncSession) -> Event:
    """Получить первое опубликованное событие из БД."""
    result = await session.execute(
        select(Event).where(Event.is_published == True).limit(1)
    )
    event = result.scalar_one_or_none()
    assert event is not None, "Нет опубликованных событий в БД"
    return event


@pytest.fixture(autouse=True)
async def cleanup_attendance(session: AsyncSession, test_user: User, test_event: Event):
    """Очистить тестовые записи посещений после каждого теста."""
    yield
    # Удаляем тестовые записи
    result = await session.execute(
        select(EventAttendance).where(
            EventAttendance.user_id == test_user.id,
            EventAttendance.event_id == test_event.id,
        )
    )
    attendance = result.scalar_one_or_none()
    if attendance:
        await session.delete(attendance)
        await session.commit()


@pytest.mark.asyncio
async def test_set_going(
    attendance_service: AttendanceService, test_user: User, test_event: Event
):
    """Тест отметки 'Я пойду'."""
    success, message = await attendance_service.set_going(test_user.id, test_event.id)

    assert success is True
    assert "✅" in message

    # Проверяем статус
    status = await attendance_service.get_user_status(test_user.id, test_event.id)
    assert status == "going"


@pytest.mark.asyncio
async def test_set_maybe(
    attendance_service: AttendanceService, test_user: User, test_event: Event
):
    """Тест отметки 'Возможно'."""
    success, message = await attendance_service.set_maybe(test_user.id, test_event.id)

    assert success is True
    assert "❓" in message

    # Проверяем статус
    status = await attendance_service.get_user_status(test_user.id, test_event.id)
    assert status == "maybe"


@pytest.mark.asyncio
async def test_remove_attendance(
    attendance_service: AttendanceService, test_user: User, test_event: Event
):
    """Тест удаления отметки о посещении."""
    # Сначала ставим отметку
    await attendance_service.set_going(test_user.id, test_event.id)

    # Удаляем
    success, message = await attendance_service.remove_attendance(test_user.id, test_event.id)

    assert success is True
    assert "🗑" in message

    # Проверяем что статус None
    status = await attendance_service.get_user_status(test_user.id, test_event.id)
    assert status is None


@pytest.mark.asyncio
async def test_get_user_status(
    attendance_service: AttendanceService, test_user: User, test_event: Event
):
    """Тест получения текущего статуса пользователя."""
    # Без отметки — None
    status = await attendance_service.get_user_status(test_user.id, test_event.id)
    assert status is None

    # После отметки — going
    await attendance_service.set_going(test_user.id, test_event.id)
    status = await attendance_service.get_user_status(test_user.id, test_event.id)
    assert status == "going"


@pytest.mark.asyncio
async def test_get_event_stats(
    attendance_service: AttendanceService, test_user: User, test_event: Event
):
    """Тест получения статистики посещений события."""
    # Ставим отметку
    await attendance_service.set_going(test_user.id, test_event.id)

    stats = await attendance_service.get_event_stats(test_event.id)

    assert "going" in stats
    assert "maybe" in stats
    assert "total" in stats
    assert stats["going"] >= 1
    assert stats["total"] >= 1


@pytest.mark.asyncio
async def test_event_not_found(attendance_service: AttendanceService, test_user: User):
    """Тест ошибки при несуществующем событии."""
    success, message = await attendance_service.set_going(test_user.id, 999999)

    assert success is False
    assert "❌" in message
    assert "не найдено" in message
