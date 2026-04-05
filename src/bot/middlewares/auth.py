"""Middleware для аутентификации пользователей."""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.repositories.user import UserRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Middleware для автоматической регистрации/обновления пользователей."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработать событие.

        Args:
            handler: Следующий обработчик
            event: Событие Telegram
            data: Данные события

        Returns:
            Any: Результат обработки
        """
        # Получаем пользователя из события
        tg_user: TgUser | None = data.get("event_from_user")

        if tg_user:
            session: AsyncSession = data["session"]
            user_repo = UserRepository(session)

            # Проверяем является ли пользователь админом
            is_admin = tg_user.id in settings.admin_ids_list

            # Получаем или создаем пользователя
            user, created = await user_repo.get_or_create(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_admin=is_admin,
            )

            if created:
                logger.info(
                    f"Новый пользователь зарегистрирован: {user.telegram_id} "
                    f"(@{user.username})"
                )
            else:
                logger.debug(f"Пользователь найден: {user.telegram_id} (@{user.username})")

            # Добавляем пользователя в данные для обработчиков
            data["user"] = user

        return await handler(event, data)
