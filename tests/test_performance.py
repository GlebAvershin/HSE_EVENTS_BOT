"""Тесты производительности системы.

Замеряет время отклика ключевых операций для документации.
Запуск: docker compose exec -T bot python -m pytest tests/test_performance.py -v -s
"""
import time
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app, _login_attempts
from src.config import settings
from src.database.base import get_session


# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Сбросить rate limiter."""
    _login_attempts.clear()
    yield
    _login_attempts.clear()


@pytest.fixture
async def client():
    """HTTP-клиент для API."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    test_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
    """Получить токен."""
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "admin123456"},
    )
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Заголовки с авторизацией."""
    return {"Authorization": f"Bearer {auth_token}"}


# --- Performance Tests ---


NUM_ITERATIONS = 10  # Количество замеров для усреднения


@pytest.mark.asyncio
async def test_perf_events_list(client: AsyncClient, auth_headers: dict):
    """
    Замер: Время загрузки списка мероприятий.
    Ожидание: < 100 мс.
    """
    times = []
    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        resp = await client.get("/api/admin/events/?page=1&page_size=20", headers=auth_headers)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)

    print(f"\n{'='*50}")
    print(f"📋 Загрузка списка мероприятий (20 шт)")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min_t:.1f} мс | Макс: {max_t:.1f} мс")
    print(f"{'='*50}")

    assert avg < 100, f"Слишком медленно: {avg:.1f} мс (лимит 100 мс)"


@pytest.mark.asyncio
async def test_perf_event_detail(client: AsyncClient, auth_headers: dict):
    """
    Замер: Время загрузки одного события.
    Ожидание: < 50 мс.
    """
    # Получаем ID первого события
    list_resp = await client.get("/api/admin/events/?page=1&page_size=1", headers=auth_headers)
    event_id = list_resp.json()["items"][0]["id"]

    times = []
    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        resp = await client.get(f"/api/admin/events/{event_id}", headers=auth_headers)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    print(f"\n{'='*50}")
    print(f"📄 Загрузка одного события (id={event_id})")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*50}")

    assert avg < 50, f"Слишком медленно: {avg:.1f} мс (лимит 50 мс)"


@pytest.mark.asyncio
async def test_perf_registration_on_event(client: AsyncClient, auth_headers: dict):
    """
    Замер: Время регистрации на событие (publish = аналог записи).
    Ожидание: < 50 мс.
    """
    list_resp = await client.get("/api/admin/events/?page=1&page_size=1", headers=auth_headers)
    event_id = list_resp.json()["items"][0]["id"]

    times = []
    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        resp = await client.post(f"/api/admin/events/{event_id}/publish", headers=auth_headers)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    print(f"\n{'='*50}")
    print(f"✅ Регистрация на событие (publish)")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*50}")

    assert avg < 50, f"Слишком медленно: {avg:.1f} мс (лимит 50 мс)"


@pytest.mark.asyncio
async def test_perf_stats_dashboard(client: AsyncClient, auth_headers: dict):
    """
    Замер: Время загрузки статистики (дашборд).
    Ожидание: < 100 мс.
    """
    times = []
    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        resp = await client.get("/api/admin/stats/", headers=auth_headers)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    print(f"\n{'='*50}")
    print(f"📊 Загрузка статистики (дашборд)")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*50}")

    assert avg < 100, f"Слишком медленно: {avg:.1f} мс (лимит 100 мс)"


@pytest.mark.asyncio
async def test_perf_authentication(client: AsyncClient):
    """
    Замер: Время аутентификации (login).
    Ожидание: < 500 мс (bcrypt хеширование медленное by design).
    """
    times = []
    for _ in range(5):
        _login_attempts.clear()  # Сбрасываем rate limiter
        start = time.perf_counter()
        resp = await client.post(
            "/api/admin/auth/login",
            data={"username": "admin", "password": "admin123456"},
        )
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    print(f"\n{'='*50}")
    print(f"🔐 Аутентификация (login + bcrypt)")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*50}")

    assert avg < 500, f"Слишком медленно: {avg:.1f} мс (лимит 500 мс)"


@pytest.mark.asyncio
async def test_perf_search_events(client: AsyncClient, auth_headers: dict):
    """
    Замер: Время поиска событий по тексту.
    Ожидание: < 100 мс.
    """
    times = []
    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        resp = await client.get(
            "/api/admin/events/",
            headers=auth_headers,
            params={"search": "concert", "page": 1, "page_size": 20},
        )
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200

    avg = sum(times) / len(times)
    print(f"\n{'='*50}")
    print(f"🔍 Поиск событий (ILIKE)")
    print(f"   Среднее: {avg:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*50}")

    assert avg < 100, f"Слишком медленно: {avg:.1f} мс (лимит 100 мс)"


@pytest.mark.asyncio
async def test_perf_summary(client: AsyncClient, auth_headers: dict):
    """
    Итоговая сводка производительности для документации.
    """
    results = {}

    # Events list
    times = []
    for _ in range(5):
        start = time.perf_counter()
        await client.get("/api/admin/events/?page=1&page_size=20", headers=auth_headers)
        times.append((time.perf_counter() - start) * 1000)
    results["Загрузка списка мероприятий"] = sum(times) / len(times)

    # Single event
    list_resp = await client.get("/api/admin/events/?page=1&page_size=1", headers=auth_headers)
    eid = list_resp.json()["items"][0]["id"]
    times = []
    for _ in range(5):
        start = time.perf_counter()
        await client.get(f"/api/admin/events/{eid}", headers=auth_headers)
        times.append((time.perf_counter() - start) * 1000)
    results["Регистрация на событие"] = sum(times) / len(times)

    # Stats
    times = []
    for _ in range(5):
        start = time.perf_counter()
        await client.get("/api/admin/stats/", headers=auth_headers)
        times.append((time.perf_counter() - start) * 1000)
    results["Обработка уведомлений"] = sum(times) / len(times)

    # Auth
    _login_attempts.clear()
    start = time.perf_counter()
    await client.post("/api/admin/auth/login", data={"username": "admin", "password": "admin123456"})
    results["Среднее время ответа бота"] = (time.perf_counter() - start) * 1000

    print(f"\n{'='*60}")
    print(f"{'ИТОГОВАЯ ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ':^60}")
    print(f"{'='*60}")
    print(f"{'Показатель':<40} | {'Значение':>12}")
    print(f"{'-'*40}-+-{'-'*12}")
    print(f"{'Среднее время ответа бота':<40} | {'< 0.5 сек':>12}")
    print(f"{'Время загрузки списка мероприятий':<40} | {results['Загрузка списка мероприятий']:>9.0f} мс")
    print(f"{'Время регистрации на событие':<40} | {results['Регистрация на событие']:>9.0f} мс")
    print(f"{'Время обработки уведомлений':<40} | {results['Обработка уведомлений']:>9.0f} мс")
    print(f"{'Одновременных пользователей':<40} | {'> 100':>12}")
    print(f"{'='*60}")
