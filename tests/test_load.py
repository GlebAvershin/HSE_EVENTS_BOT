"""Нагрузочный тест: имитация 100+ одновременных пользователей.

Запуск: docker compose exec -T bot python -m pytest tests/test_load.py -v -s
"""
import asyncio
import time
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app, _login_attempts
from src.config import settings
from src.database.base import get_session


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    _login_attempts.clear()
    yield
    _login_attempts.clear()


@pytest.fixture
async def client():
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=20, max_overflow=30)
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
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "admin123456"},
    )
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


async def simulate_user_request(client: AsyncClient, headers: dict, user_id: int) -> dict:
    """Имитация одного пользователя: загрузка списка событий."""
    start = time.perf_counter()
    resp = await client.get(
        "/api/admin/events/",
        headers=headers,
        params={"page": 1, "page_size": 20},
    )
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "user_id": user_id,
        "status": resp.status_code,
        "time_ms": elapsed,
    }


async def simulate_mixed_load(client: AsyncClient, headers: dict, user_id: int) -> dict:
    """Имитация пользователя с разными запросами (mixed workload)."""
    start = time.perf_counter()
    
    # Каждый пользователь делает 3 запроса подряд (типичная сессия)
    # 1. Список событий
    r1 = await client.get("/api/admin/events/", headers=headers, params={"page": 1, "page_size": 5})
    
    # 2. Детали первого события
    items = r1.json().get("items", [])
    if items:
        event_id = items[user_id % len(items)]["id"]
        r2 = await client.get(f"/api/admin/events/{event_id}", headers=headers)
    
    # 3. Статистика
    r3 = await client.get("/api/admin/stats/", headers=headers)
    
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "user_id": user_id,
        "status": r1.status_code,
        "time_ms": elapsed,
        "requests": 3,
    }


@pytest.mark.asyncio
async def test_load_100_concurrent_users(client: AsyncClient, auth_headers: dict):
    """
    Нагрузочный тест: 100 одновременных запросов к списку событий.
    Имитирует 100 пользователей, одновременно загружающих список мероприятий.
    """
    NUM_USERS = 100

    print(f"\n{'='*60}")
    print(f"🔥 НАГРУЗОЧНЫЙ ТЕСТ: {NUM_USERS} одновременных пользователей")
    print(f"   Операция: GET /api/admin/events/ (список мероприятий)")
    print(f"{'='*60}")

    # Запускаем 100 запросов одновременно
    start_total = time.perf_counter()
    tasks = [
        simulate_user_request(client, auth_headers, i)
        for i in range(NUM_USERS)
    ]
    results = await asyncio.gather(*tasks)
    total_time = (time.perf_counter() - start_total) * 1000

    # Анализ результатов
    times = [r["time_ms"] for r in results]
    statuses = [r["status"] for r in results]
    success_count = statuses.count(200)
    error_count = NUM_USERS - success_count

    avg_time = sum(times) / len(times)
    p50 = sorted(times)[len(times) // 2]
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]
    rps = NUM_USERS / (total_time / 1000)

    print(f"\n📊 Результаты:")
    print(f"   Успешных: {success_count}/{NUM_USERS} ({success_count/NUM_USERS*100:.0f}%)")
    print(f"   Ошибок: {error_count}")
    print(f"   Общее время: {total_time:.0f} мс")
    print(f"   RPS: {rps:.0f} запросов/сек")
    print(f"\n⏱  Время отклика:")
    print(f"   Среднее: {avg_time:.1f} мс")
    print(f"   P50: {p50:.1f} мс")
    print(f"   P95: {p95:.1f} мс")
    print(f"   P99: {p99:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*60}")

    # Assertions
    assert success_count == NUM_USERS, f"Не все запросы успешны: {error_count} ошибок"
    assert avg_time < 1000, f"Среднее время > 1000мс: {avg_time:.0f} мс"


@pytest.mark.asyncio
async def test_load_150_concurrent_users(client: AsyncClient, auth_headers: dict):
    """
    Нагрузочный тест: 150 одновременных запросов.
    Проверяет что система выдерживает нагрузку выше заявленных 100 пользователей.
    """
    NUM_USERS = 150

    print(f"\n{'='*60}")
    print(f"🔥 НАГРУЗОЧНЫЙ ТЕСТ: {NUM_USERS} одновременных пользователей")
    print(f"   Операция: GET /api/admin/events/ (список мероприятий)")
    print(f"{'='*60}")

    start_total = time.perf_counter()
    tasks = [
        simulate_user_request(client, auth_headers, i)
        for i in range(NUM_USERS)
    ]
    results = await asyncio.gather(*tasks)
    total_time = (time.perf_counter() - start_total) * 1000

    times = [r["time_ms"] for r in results]
    success_count = [r["status"] for r in results].count(200)
    rps = NUM_USERS / (total_time / 1000)

    avg_time = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"\n📊 Результаты:")
    print(f"   Успешных: {success_count}/{NUM_USERS}")
    print(f"   RPS: {rps:.0f} запросов/сек")
    print(f"   Среднее: {avg_time:.1f} мс | P95: {p95:.1f} мс")
    print(f"{'='*60}")

    assert success_count == NUM_USERS
    assert avg_time < 1000


@pytest.mark.asyncio
async def test_load_mixed_workload_100_users(client: AsyncClient, auth_headers: dict):
    """
    Нагрузочный тест: 100 пользователей с mixed workload.
    Каждый пользователь делает 3 запроса (список → детали → статистика).
    Итого: 300 запросов от 100 пользователей.
    """
    NUM_USERS = 100

    print(f"\n{'='*60}")
    print(f"🔥 НАГРУЗОЧНЫЙ ТЕСТ: {NUM_USERS} пользователей, mixed workload")
    print(f"   Каждый: список → детали события → статистика (3 запроса)")
    print(f"   Итого запросов: {NUM_USERS * 3}")
    print(f"{'='*60}")

    start_total = time.perf_counter()
    tasks = [
        simulate_mixed_load(client, auth_headers, i)
        for i in range(NUM_USERS)
    ]
    results = await asyncio.gather(*tasks)
    total_time = (time.perf_counter() - start_total) * 1000

    times = [r["time_ms"] for r in results]
    total_requests = sum(r["requests"] for r in results)
    success_count = [r["status"] for r in results].count(200)
    rps = total_requests / (total_time / 1000)

    avg_time = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"\n📊 Результаты:")
    print(f"   Пользователей: {success_count}/{NUM_USERS} успешно")
    print(f"   Всего запросов: {total_requests}")
    print(f"   Общее время: {total_time:.0f} мс")
    print(f"   RPS: {rps:.0f} запросов/сек")
    print(f"\n⏱  Время на пользователя (3 запроса):")
    print(f"   Среднее: {avg_time:.1f} мс")
    print(f"   P95: {p95:.1f} мс")
    print(f"   Мин: {min(times):.1f} мс | Макс: {max(times):.1f} мс")
    print(f"{'='*60}")

    assert success_count == NUM_USERS
    assert avg_time < 1000


@pytest.mark.asyncio
async def test_load_summary(client: AsyncClient, auth_headers: dict):
    """
    Итоговая сводка нагрузочного тестирования для документации.
    """
    print(f"\n{'='*60}")
    print(f"{'ИТОГИ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ':^60}")
    print(f"{'='*60}")

    # 100 concurrent
    tasks = [simulate_user_request(client, auth_headers, i) for i in range(100)]
    start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    t100 = (time.perf_counter() - start) * 1000
    times_100 = [r["time_ms"] for r in results]
    success_100 = [r["status"] for r in results].count(200)

    # 200 concurrent
    tasks = [simulate_user_request(client, auth_headers, i) for i in range(200)]
    start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    t200 = (time.perf_counter() - start) * 1000
    times_200 = [r["time_ms"] for r in results]
    success_200 = [r["status"] for r in results].count(200)

    print(f"\n{'Нагрузка':<20} | {'Успех':>8} | {'Ср.время':>10} | {'P95':>8} | {'RPS':>6}")
    print(f"{'-'*20}-+-{'-'*8}-+-{'-'*10}-+-{'-'*8}-+-{'-'*6}")
    print(f"{'100 пользователей':<20} | {success_100:>5}/100 | {sum(times_100)/100:>7.0f} мс | {sorted(times_100)[95]:>5.0f} мс | {100/(t100/1000):>5.0f}")
    print(f"{'200 пользователей':<20} | {success_200:>5}/200 | {sum(times_200)/200:>7.0f} мс | {sorted(times_200)[190]:>5.0f} мс | {200/(t200/1000):>5.0f}")
    print(f"\n✅ Система выдерживает более 100 одновременных пользователей")
    print(f"{'='*60}")

    assert success_100 == 100
    assert success_200 == 200
