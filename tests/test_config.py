"""Тесты конфигурации."""
import pytest
from src.config import settings


def test_settings_loaded():
    """Проверка загрузки настроек."""
    assert settings.BOT_TOKEN is not None
    assert settings.DB_NAME == "nn_events"
    assert settings.DB_PORT == 5432


def test_database_url():
    """Проверка формирования URL базы данных."""
    db_url = settings.database_url
    assert "postgresql+asyncpg://" in db_url
    assert settings.DB_NAME in db_url
    assert settings.DB_HOST in db_url


def test_redis_url():
    """Проверка формирования URL Redis."""
    redis_url = settings.redis_url
    assert "redis://" in redis_url
    assert str(settings.REDIS_PORT) in redis_url


def test_admin_ids_list():
    """Проверка парсинга списка админов."""
    admin_ids = settings.admin_ids_list
    assert isinstance(admin_ids, list)
    if settings.ADMIN_IDS:
        assert len(admin_ids) > 0
        assert all(isinstance(admin_id, int) for admin_id in admin_ids)
