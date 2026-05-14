"""Планировщик автоматического парсинга событий."""
import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.parsers.parser_manager import ParserManager
from src.database.base import async_session_maker


class ParsingScheduler:
    """
    Планировщик парсинга событий.
    
    Выполняет две задачи:
    1. Парсинг новых событий (ежедневно в 6:00 и 18:00)
    2. Удаление прошедших событий (ежедневно в 3:00)
    """
    
    def __init__(self):
        """Инициализация планировщика."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def parse_events_job(self):
        """Задача парсинга новых событий."""
        print(f"\n{'='*50}")
        print(f"[PARSE] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        try:
            async with async_session_maker() as session:
                manager = ParserManager(session)
                stats = await manager.parse_all()
                
                print(f"\n{'='*50}")
                print(f"[PARSE] Completed at {datetime.now().strftime('%H:%M:%S')}")
                print(f"  Found: {stats['total_parsed']}")
                print(f"  Saved new: {stats['total_saved']}")
                if stats['errors']:
                    print(f"  Errors: {len(stats['errors'])}")
                    for error in stats['errors']:
                        print(f"    - {error}")
                print(f"{'='*50}\n")
                
                if stats['total_saved'] > 0:
                    await self._notify_users_about_new_events(stats['total_saved'])
        
        except Exception as e:
            print(f"[PARSE ERROR] {type(e).__name__}: {e}")
    
    async def cleanup_past_events_job(self):
        """
        Задача удаления прошедших событий.
        
        Удаляет события, у которых date_start < сейчас - 1 день.
        Оставляем буфер в 1 день, чтобы пользователи могли видеть
        события, которые прошли сегодня.
        """
        print(f"\n[CLEANUP] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            async with async_session_maker() as session:
                from sqlalchemy import delete, select, func
                from src.database.models.event import Event
                from src.database.models.attendance import EventAttendance
                
                # Граница: события старше 1 дня считаются прошедшими
                cutoff = datetime.utcnow() - timedelta(days=1)
                
                # Сначала считаем сколько удалим
                count_result = await session.execute(
                    select(func.count()).select_from(Event).where(Event.date_start < cutoff)
                )
                count = count_result.scalar() or 0
                
                if count == 0:
                    print(f"[CLEANUP] No past events to remove")
                    return
                
                # Удаляем связанные записи посещений
                # (ON DELETE CASCADE должен сработать, но на всякий случай)
                past_event_ids = await session.execute(
                    select(Event.id).where(Event.date_start < cutoff)
                )
                ids = [row[0] for row in past_event_ids.all()]
                
                if ids:
                    await session.execute(
                        delete(EventAttendance).where(EventAttendance.event_id.in_(ids))
                    )
                    
                    # Удаляем сами события
                    await session.execute(
                        delete(Event).where(Event.id.in_(ids))
                    )
                    
                    await session.commit()
                
                print(f"[CLEANUP] Removed {count} past events (before {cutoff.strftime('%Y-%m-%d')})")
        
        except Exception as e:
            print(f"[CLEANUP ERROR] {type(e).__name__}: {e}")
    
    async def _notify_users_about_new_events(self, count: int):
        """Уведомить пользователей о новых событиях."""
        try:
            from aiogram import Bot
            from src.config import settings
            
            bot = Bot(token=settings.BOT_TOKEN)
            
            async with async_session_maker() as session:
                from sqlalchemy import select
                from src.database.models.user import User
                from src.database.models.user_settings import UserSettings
                
                result = await session.execute(
                    select(User, UserSettings)
                    .join(UserSettings, User.id == UserSettings.user_id)
                    .where(UserSettings.notify_new_events == True)
                )
                
                users_with_settings = result.all()
                
                message = (
                    f"🎉 <b>Новые события!</b>\n\n"
                    f"Добавлено {count} новых событий в Нижнем Новгороде.\n\n"
                    f"Посмотреть: /events"
                )
                
                sent_count = 0
                for user, user_settings in users_with_settings:
                    try:
                        await bot.send_message(user.telegram_id, message)
                        sent_count += 1
                    except Exception:
                        continue
                
                if sent_count > 0:
                    print(f"[NOTIFY] Sent to {sent_count} users about {count} new events")
            
            await bot.session.close()
        
        except Exception as e:
            print(f"[NOTIFY ERROR] {e}")
    
    async def event_reminders_job(self):
        """
        Задача отправки напоминаний о предстоящих событиях.
        
        Проверяет события, которые начнутся через ~24ч или ~1ч,
        и отправляет напоминания пользователям со статусом "going",
        у которых включены напоминания в настройках.
        """
        try:
            from aiogram import Bot
            from src.config import settings
            from sqlalchemy import select, and_
            from src.database.models.event import Event
            from src.database.models.attendance import EventAttendance
            from src.database.models.user import User
            from src.database.models.user_settings import UserSettings
            
            bot = Bot(token=settings.BOT_TOKEN)
            
            async with async_session_maker() as session:
                now = datetime.utcnow()
                sent_count = 0
                
                # Проверяем два окна: 24ч (23.5-24.5ч) и 1ч (0.5-1.5ч)
                windows = [
                    (timedelta(hours=23, minutes=30), timedelta(hours=24, minutes=30), "завтра"),
                    (timedelta(minutes=30), timedelta(hours=1, minutes=30), "через 1 час"),
                ]
                
                for window_start, window_end, time_text in windows:
                    start = now + window_start
                    end = now + window_end
                    
                    # Находим события в этом окне
                    events_result = await session.execute(
                        select(Event).where(
                            and_(
                                Event.date_start >= start,
                                Event.date_start <= end,
                                Event.is_published == True,
                            )
                        )
                    )
                    events = events_result.scalars().all()
                    
                    for event in events:
                        # Находим участников со статусом "going" и включёнными напоминаниями
                        attendees_result = await session.execute(
                            select(User, UserSettings)
                            .join(EventAttendance, User.id == EventAttendance.user_id)
                            .join(UserSettings, User.id == UserSettings.user_id)
                            .where(
                                and_(
                                    EventAttendance.event_id == event.id,
                                    EventAttendance.status == "going",
                                    UserSettings.notify_event_reminder == True,
                                )
                            )
                        )
                        attendees = attendees_result.all()
                        
                        if not attendees:
                            continue
                        
                        # Формируем сообщение
                        text = (
                            f"⏰ <b>Напоминание о событии!</b>\n\n"
                            f"Событие начнётся {time_text}:\n\n"
                            f"📅 <b>{event.title}</b>\n"
                            f"📆 {event.date_start.strftime('%d.%m.%Y %H:%M')}\n"
                        )
                        if event.location:
                            text += f"📍 {event.location}\n"
                        if event.address:
                            text += f"🗺 {event.address}\n"
                        text += f"\nНе опоздайте! 🎉"
                        
                        for user, user_settings in attendees:
                            try:
                                await bot.send_message(user.telegram_id, text)
                                sent_count += 1
                            except Exception:
                                continue
                
                if sent_count > 0:
                    print(f"[REMIND] Sent {sent_count} reminders")
            
            await bot.session.close()
        
        except Exception as e:
            print(f"[REMIND ERROR] {type(e).__name__}: {e}")

    def start(self, interval_hours: int = 12):
        """
        Запустить планировщик.
        
        Расписание:
        - Парсинг: каждые interval_hours часов (по умолчанию 12ч = 2 раза в день)
        - Очистка: ежедневно в 03:00
        - Первый парсинг: через 30 секунд после старта
        
        Args:
            interval_hours: Интервал парсинга в часах
        """
        if self.is_running:
            print("Scheduler is already running")
            return
        
        # Парсинг каждые N часов
        self.scheduler.add_job(
            self.parse_events_job,
            trigger=IntervalTrigger(hours=interval_hours),
            id="parse_events",
            name="Parse events from all sources",
            replace_existing=True,
        )
        
        # Очистка прошедших событий — ежедневно в 03:00
        self.scheduler.add_job(
            self.cleanup_past_events_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_past_events",
            name="Remove past events",
            replace_existing=True,
        )
        
        # Напоминания о событиях — каждый час
        self.scheduler.add_job(
            self.event_reminders_job,
            trigger=IntervalTrigger(hours=1),
            id="event_reminders",
            name="Send event reminders (24h and 1h before)",
            replace_existing=True,
        )
        
        # Первый парсинг через 30 секунд после старта
        self.scheduler.add_job(
            self.parse_events_job,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=30),
            id="parse_events_startup",
            name="Parse events on startup",
        )
        
        # Первая очистка через 60 секунд после старта
        self.scheduler.add_job(
            self.cleanup_past_events_job,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=60),
            id="cleanup_startup",
            name="Cleanup on startup",
        )
        
        self.scheduler.start()
        self.is_running = True
        
        print(f"[OK] Scheduler started:")
        print(f"     Parsing: every {interval_hours}h (first in 30s)")
        print(f"     Cleanup: daily at 03:00 (first in 60s)")
        print(f"     Reminders: every 1h (24h and 1h before events)")
    
    def _write_heartbeat(self):
        """Записать heartbeat файл для Docker healthcheck."""
        try:
            with open("/tmp/bot_heartbeat", "w") as f:
                f.write(str(datetime.now()))
        except Exception:
            pass

    def stop(self):
        """Остановить планировщик."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        print("[STOP] Scheduler stopped")
    
    async def run_manual_parsing(self):
        """Запустить парсинг вручную (для админки)."""
        await self.parse_events_job()
    
    async def run_manual_cleanup(self):
        """Запустить очистку вручную (для админки)."""
        await self.cleanup_past_events_job()


# Глобальный экземпляр планировщика
parsing_scheduler = ParsingScheduler()
