"""Обработчики админ-команд."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User
from src.parsers.parser_manager import ParserManager

router = Router()


def is_admin(user: User) -> bool:
    """
    Проверить является ли пользователь админом.
    
    Args:
        user: Пользователь
        
    Returns:
        True если админ
    """
    return user.is_admin


@router.message(Command("admin_parse"))
async def cmd_admin_parse(message: Message, user: User, session: AsyncSession):
    """
    Запустить парсинг событий вручную.
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
        session: Сессия БД
    """
    if not is_admin(user):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    await message.answer("🔄 Запускаю парсинг событий...\nЭто может занять несколько минут.")
    
    try:
        manager = ParserManager(session)
        stats = await manager.parse_all()
        
        text = (
            f"✅ <b>Парсинг завершен!</b>\n\n"
            f"📊 Статистика:\n"
            f"• Найдено событий: {stats['total_parsed']}\n"
            f"• Сохранено новых: {stats['total_saved']}\n"
        )
        
        if stats['errors']:
            text += f"\n⚠️ Ошибок: {len(stats['errors'])}\n"
            for error in stats['errors'][:5]:  # Показать первые 5 ошибок
                text += f"  - {error}\n"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при парсинге: {str(e)}")


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message, user: User, session: AsyncSession):
    """
    Показать статистику системы.
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
        session: Сессия БД
    """
    if not is_admin(user):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        from sqlalchemy import select, func
        from src.database.models.event import Event
        from src.database.models.user import User as UserModel
        from src.database.models.friendship import Friendship
        from src.database.models.attendance import EventAttendance
        
        # Подсчитать статистику
        users_count = await session.scalar(select(func.count()).select_from(UserModel))
        events_count = await session.scalar(select(func.count()).select_from(Event))
        friendships_count = await session.scalar(
            select(func.count()).select_from(Friendship).where(Friendship.status == "accepted")
        )
        attendances_count = await session.scalar(select(func.count()).select_from(EventAttendance))
        
        # События по категориям
        it_events = await session.scalar(
            select(func.count()).select_from(Event).where(Event.category == "it")
        )
        entertainment_events = await session.scalar(
            select(func.count()).select_from(Event).where(Event.category == "entertainment")
        )
        
        text = (
            f"📊 <b>Статистика системы</b>\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"📅 Событий: {events_count}\n"
            f"  • IT: {it_events}\n"
            f"  • Развлечения: {entertainment_events}\n"
            f"👫 Дружб: {friendships_count // 2}\n"  # Делим на 2 т.к. двусторонние
            f"✅ Записей на события: {attendances_count}\n"
        )
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении статистики: {str(e)}")


@router.message(Command("admin_help"))
async def cmd_admin_help(message: Message, user: User):
    """
    Показать справку по админ-командам.
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
    """
    if not is_admin(user):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    text = (
        f"🛠 <b>Админ-команды</b>\n\n"
        f"/admin_stats - Статистика системы\n"
        f"/admin_parse - Запустить парсинг событий\n"
        f"/admin_help - Эта справка\n"
    )
    
    await message.answer(text)
