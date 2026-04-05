"""Тесты импортов модулей бота."""


def test_import_bot_main():
    """Тест импорта главного модуля бота."""
    from src.bot import main
    assert main is not None


def test_import_handlers():
    """Тест импорта обработчиков."""
    from src.bot.handlers import start, events, friends
    assert start.router is not None
    assert events.router is not None
    assert friends.router is not None


def test_import_keyboards():
    """Тест импорта клавиатур."""
    from src.bot.keyboards.main_menu import get_main_menu
    from src.bot.keyboards.events import get_events_category_keyboard
    from src.bot.keyboards.friends import get_friends_menu_keyboard
    assert get_main_menu is not None
    assert get_events_category_keyboard is not None
    assert get_friends_menu_keyboard is not None


def test_import_middlewares():
    """Тест импорта middleware."""
    from src.bot.middlewares import AuthMiddleware
    assert AuthMiddleware is not None


def test_import_repositories():
    """Тест импорта репозиториев."""
    from src.database.repositories.user import UserRepository
    from src.database.repositories.event import EventRepository
    from src.database.repositories.friendship import FriendshipRepository
    assert UserRepository is not None
    assert EventRepository is not None
    assert FriendshipRepository is not None


def test_import_services():
    """Тест импорта сервисов."""
    from src.services.event_service import EventService
    from src.services.friendship_service import FriendshipService
    assert EventService is not None
    assert FriendshipService is not None
