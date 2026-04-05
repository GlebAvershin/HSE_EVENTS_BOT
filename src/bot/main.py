"""Главный файл Telegram бота."""
import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.config import settings
from src.database.base import engine, async_session_maker
from src.bot.handlers import start
from src.bot.middlewares import AuthMiddleware
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def on_startup(bot: Bot):
    """
    Действия при запуске бота.

    Args:
        bot: Экземпляр бота
    """
    logger.info("Бот запускается...")
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username}")


async def on_shutdown(bot: Bot):
    """
    Действия при остановке бота.

    Args:
        bot: Экземпляр бота
    """
    logger.info("Бот останавливается...")
    await bot.session.close()
    await engine.dispose()
    logger.info("Бот остановлен")


async def main():
    """Главная функция запуска бота."""
    # Проверка токена
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "test_token_replace_with_real":
        logger.error("❌ BOT_TOKEN не настроен в .env файле!")
        logger.error("Получите токен у @BotFather и добавьте в .env")
        sys.exit(1)

    # Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Middleware для передачи сессии БД (должен быть ПЕРВЫМ)
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)

    # Регистрация middleware (после db_session_middleware)
    dp.update.middleware(AuthMiddleware())

    # Регистрация роутеров
    dp.include_router(start.router)
    
    # Импортируем и регистрируем обработчики событий
    from src.bot.handlers import events
    dp.include_router(events.router)
    
    # Импортируем и регистрируем обработчики друзей
    from src.bot.handlers import friends
    dp.include_router(friends.router)
    
    # Импортируем и регистрируем обработчики календаря
    from src.bot.handlers import calendar
    dp.include_router(calendar.router)
    
    # Импортируем и регистрируем обработчики профиля
    from src.bot.handlers import profile
    dp.include_router(profile.router)

    # Регистрация событий
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск бота
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
