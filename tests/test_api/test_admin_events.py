"""Тесты API управления событиями в админ-панели."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict):
    """Тест получения списка событий с пагинацией."""
    resp = await client.get("/api/admin/events/", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert isinstance(data["items"], list)
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_list_events_filter_category(client: AsyncClient, auth_headers: dict):
    """Тест фильтрации событий по категории."""
    resp = await client.get(
        "/api/admin/events/", headers=auth_headers, params={"category": "it"}
    )

    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["category"] == "it"


@pytest.mark.asyncio
async def test_list_events_filter_status(client: AsyncClient, auth_headers: dict):
    """Тест фильтрации событий по статусу published."""
    resp = await client.get(
        "/api/admin/events/", headers=auth_headers, params={"status": "published"}
    )

    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["is_published"] is True


@pytest.mark.asyncio
async def test_list_events_search(client: AsyncClient, auth_headers: dict):
    """Тест поиска событий по тексту."""
    resp = await client.get(
        "/api/admin/events/", headers=auth_headers, params={"search": "Нижн"}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_event(client: AsyncClient, auth_headers: dict):
    """Тест получения одного события по ID."""
    # Сначала получаем список, чтобы взять реальный ID
    list_resp = await client.get("/api/admin/events/", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]

    if items:
        event_id = items[0]["id"]
        resp = await client.get(f"/api/admin/events/{event_id}", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == event_id
        assert "title" in data
        assert "category" in data
        assert "date_start" in data


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient, auth_headers: dict):
    """Тест получения несуществующего события — 404."""
    resp = await client.get("/api/admin/events/999999", headers=auth_headers)

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_publish_event(client: AsyncClient, auth_headers: dict):
    """Тест публикации события."""
    # Получаем список событий
    list_resp = await client.get("/api/admin/events/", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]

    if items:
        event_id = items[0]["id"]
        resp = await client.post(
            f"/api/admin/events/{event_id}/publish", headers=auth_headers
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_published"] is True
        assert data["is_moderated"] is True


@pytest.mark.asyncio
async def test_delete_event(client: AsyncClient, auth_headers: dict):
    """Тест удаления события — создаём и удаляем."""
    # Создаём тестовое событие для удаления
    create_resp = await client.post(
        "/api/admin/events/",
        headers=auth_headers,
        json={
            "title": "Тестовое событие для удаления",
            "category": "it",
            "date_start": "2026-12-31T23:00:00",
            "description": "Будет удалено",
        },
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # Удаляем
    resp = await client.delete(f"/api/admin/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Проверяем что удалено
    get_resp = await client.get(f"/api/admin/events/{event_id}", headers=auth_headers)
    assert get_resp.status_code == 404
