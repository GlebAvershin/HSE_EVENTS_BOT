"""Общие фикстуры для API тестов."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app, _login_attempts
from src.config import settings
from src.database.base import get_session


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Сбросить rate limiter перед каждым тестом."""
    _login_attempts.clear()
    yield
    _login_attempts.clear()


@pytest.fixture
async def client():
    """Создать HTTP-клиент для тестирования API с изолированной сессией БД."""
    # Создаём свежий engine для каждого теста, чтобы избежать
    # проблем с закрытым event loop
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    test_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_session():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def auth_token(client: AsyncClient) -> str:
    """Получить токен аутентификации."""
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "admin123456"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Заголовки с авторизацией."""
    return {"Authorization": f"Bearer {auth_token}"}
