"""Тесты аутентификации админ-панели."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Тест успешной аутентификации с валидными данными."""
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "admin123456"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Тест аутентификации с неверным паролем — 401."""
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "admin", "password": "wrong_password"},
    )

    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_username(client: AsyncClient):
    """Тест аутентификации с несуществующим пользователем — 401."""
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "nonexistent_user", "password": "any_password"},
    )

    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client: AsyncClient):
    """Тест доступа к защищённому эндпоинту без токена — 401."""
    resp = await client.get("/api/admin/events/")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_invalid_token(client: AsyncClient):
    """Тест доступа к защищённому эндпоинту с невалидным токеном — 401."""
    resp = await client.get(
        "/api/admin/events/",
        headers={"Authorization": "Bearer invalid_token_here"},
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_valid_token(client: AsyncClient, auth_headers: dict):
    """Тест доступа к защищённому эндпоинту с валидным токеном — 200."""
    resp = await client.get(
        "/api/admin/events/",
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
