"""Главный файл Telegram бота."""
import asyncio
import os
import sys
import time

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

# Глобальный timestamp последнего успешного update от Telegram
_last_successful_poll = time.time()
_WATCHDOG_TIMEOUT = 300  # 5 минут без связи = перезапуск


async def on_startup(bot: Bot):
    """Действия при запуске бота."""
    logger.info("Бот запускается...")
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username}")
    
    # Запустить автоматический парсинг и очистку событий
    from src.parsers.scheduler import parsing_scheduler
    parsing_scheduler.start(interval_hours=12)
    logger.info("Планировщик запущен: парсинг каждые 12ч, очистка прошедших в 03:00")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота."""
    logger.info("Бот останавливается...")
    
    from src.parsers.scheduler import parsing_scheduler
    parsing_scheduler.stop()
    
    await bot.session.close()
    await engine.dispose()
    logger.info("Бот остановлен")


async def watchdog():
    """
    Watchdog: проверяет что бот жив и получает updates.
    Если polling завис на retry более 5 минут — убивает процесс.
    Docker restart policy перезапустит контейнер.
    """
    global _last_successful_poll
    
    while True:
        await asyncio.sleep(30)
        
        # Обновляем heartbeat файл
        try:
            with open("/tmp/bot_heartbeat", "w") as f:
                f.write(str(time.time()))
        except Exception:
            pass
        
        # Проверяем таймаут
        elapsed = time.time() - _last_successful_poll
        if elapsed > _WATCHDOG_TIMEOUT:
            logger.error(
                f"WATCHDOG: Нет связи с Telegram {int(elapsed)} сек "
                f"(лимит {_WATCHDOG_TIMEOUT} сек). Перезапуск..."
            )
            # Принудительное завершение — Docker перезапустит
            os._exit(1)


async def main():
    """Главная функция запуска бота."""
    global _last_successful_poll
    
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "test_token_replace_with_real":
        logger.error("❌ BOT_TOKEN не настроен в .env файле!")
        sys.exit(1)

    # Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Middleware для передачи сессии БД
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)

    # Middleware для отслеживания активности (обновляет watchdog)
    @dp.update.middleware()
    async def activity_middleware(handler, event, data):
        global _last_successful_poll
        _last_successful_poll = time.time()
        return await handler(event, data)

    # Регистрация middleware
    dp.update.middleware(AuthMiddleware())

    # Регистрация роутеров
    dp.include_router(start.router)
    
    from src.bot.handlers import events
    dp.include_router(events.router)
    
    from src.bot.handlers import friends
    dp.include_router(friends.router)
    
    from src.bot.handlers import calendar
    dp.include_router(calendar.router)
    
    from src.bot.handlers import profile
    dp.include_router(profile.router)
    
    from src.bot.handlers import admin
    dp.include_router(admin.router)

    # Регистрация событий
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск watchdog как фоновую задачу
    watchdog_task = asyncio.create_task(watchdog())

    # Обновляем timestamp при старте
    _last_successful_poll = time.time()

    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        watchdog_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except SystemExit:
        pass  # os._exit() из watchdog
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
