"""Базовые настройки для работы с БД."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

# Создание движка БД
engine = create_async_engine(
    settings.database_url,
    echo=settings.LOG_LEVEL == "DEBUG",
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=5,
    max_overflow=10,
    connect_args={
        "server_settings": {
            "application_name": "nn_events_bot",
        },
        "command_timeout": 60,
    },
)

# Фабрика сессий
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для моделей
Base = declarative_base()


async def get_session() -> AsyncSession:
    """
    Получить сессию БД.

    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session_maker() as session:
        yield session
