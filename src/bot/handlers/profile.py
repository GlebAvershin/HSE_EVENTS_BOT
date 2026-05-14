"""Обработчики для работы с профилем пользователя."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.profile import get_profile_menu_keyboard, get_settings_keyboard
from src.bot.keyboards.main_menu import get_main_menu
from src.database.models.user import User
from src.database.repositories.user import UserRepository

router = Router()


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message, user: User, session: AsyncSession):
    """
    Обработчик команды /profile и кнопки "Профиль".

    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
        session: Сессия БД
    """
    # Получаем настройки пользователя
    from src.database.models.user_settings import UserSettings
    from sqlalchemy import select
    
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    
    # Формируем информацию о профиле
    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"Имя: {user.first_name or 'Не указано'}\n"
    )
    
    if user.username:
        text += f"Username: @{user.username}\n"
    
    # Статистика
    from src.database.repositories.friendship import FriendshipRepository
    from src.database.repositories.attendance import AttendanceRepository
    
    friendship_repo = FriendshipRepository(session)
    attendance_repo = AttendanceRepository(session)
    
    friends = await friendship_repo.get_friends(user.id)
    events_going = await attendance_repo.get_user_events(user.id, status="going")
    
    text += f"\n📊 <b>Статистика:</b>\n"
    text += f"👥 Друзей: {len(friends)}\n"
    text += f"📅 Событий запланировано: {len(events_going)}\n"
    
    # Настройки уведомлений
    if settings:
        text += f"\n🔔 <b>Уведомления:</b>\n"
        text += f"• Друзья на событиях: {'✅' if settings.notify_friend_going else '❌'}\n"
        text += f"• Новые события: {'✅' if settings.notify_new_events else '❌'}\n"
        text += f"• Напоминания: {'✅' if settings.notify_event_reminder else '❌'}\n"
        text += f"\n🔒 <b>Приватность:</b>\n"
        text += f"• Скрыть посещения: {'✅' if settings.hide_attendance else '❌'}\n"
        text += f"• Скрыть из поиска: {'✅' if settings.hide_from_search else '❌'}\n"
    
    await message.answer(text, reply_markup=get_profile_menu_keyboard())


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, user: User, session: AsyncSession):
    """
    Показать настройки пользователя.

    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
        session: Сессия БД
    """
    # Получаем настройки
    from src.database.models.user_settings import UserSettings
    from sqlalchemy import select
    
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        await message.answer("❌ Настройки не найдены")
        return
    
    text = (
        f"⚙️ <b>Настройки уведомлений</b>\n\n"
        f"Управляйте типами уведомлений, которые вы хотите получать:"
    )
    
    await message.answer(text, reply_markup=get_settings_keyboard(settings))


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_setting(callback: CallbackQuery, user: User, session: AsyncSession):
    """
    Переключить настройку уведомлений.

    Args:
        callback: Callback query
        user: Пользователь из БД
        session: Сессия БД
    """
    setting_name = callback.data.replace("toggle_", "")
    
    # Получаем настройки
    from src.database.models.user_settings import UserSettings
    from sqlalchemy import select
    
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        await callback.answer("❌ Настройки не найдены", show_alert=True)
        return
    
    # Переключаем настройку
    if setting_name == "friend_going":
        settings.notify_friend_going = not settings.notify_friend_going
        status = "включены" if settings.notify_friend_going else "выключены"
        message = f"🔔 Уведомления о друзьях на событиях {status}"
    elif setting_name == "new_events":
        settings.notify_new_events = not settings.notify_new_events
        status = "включены" if settings.notify_new_events else "выключены"
        message = f"🔔 Уведомления о новых событиях {status}"
    elif setting_name == "event_reminder":
        settings.notify_event_reminder = not settings.notify_event_reminder
        status = "включены" if settings.notify_event_reminder else "выключены"
        message = f"🔔 Напоминания о событиях {status}"
    elif setting_name == "hide_attendance":
        settings.hide_attendance = not settings.hide_attendance
        status = "включено" if settings.hide_attendance else "выключено"
        message = f"🔒 Скрытие посещений {status}"
    elif setting_name == "hide_from_search":
        settings.hide_from_search = not settings.hide_from_search
        status = "включено" if settings.hide_from_search else "выключено"
        message = f"🔒 Скрытие из поиска {status}"
    else:
        await callback.answer("❌ Неизвестная настройка", show_alert=True)
        return
    
    await session.commit()
    
    # Обновляем клавиатуру
    text = (
        f"⚙️ <b>Настройки уведомлений</b>\n\n"
        f"Управляйте типами уведомлений, которые вы хотите получать:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard(settings))
    await callback.answer(message)


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, user: User, session: AsyncSession):
    """
    Вернуться к профилю.

    Args:
        callback: Callback query
        user: Пользователь из БД
        session: Сессия БД
    """
    await callback.message.delete()
    await cmd_profile(callback.message, user, session)
    await callback.answer()
