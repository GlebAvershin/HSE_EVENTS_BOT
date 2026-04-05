"""Обработчики для работы с календарем."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.calendar import get_calendar_menu_keyboard, get_calendar_period_keyboard
from src.bot.keyboards.main_menu import get_main_menu
from src.bot.keyboards.events import get_events_list_keyboard
from src.services.calendar_service import CalendarService

router = Router()


@router.message(Command("calendar"))
@router.message(F.text == "📆 Календарь")
async def cmd_calendar(message: Message):
    """
    Обработчик команды /calendar и кнопки "Календарь".

    Args:
        message: Сообщение от пользователя
    """
    text = (
        "📆 <b>Календарь событий</b>\n\n"
        "Выберите период для просмотра событий:\n\n"
        "📅 <b>Сегодня</b> - события на сегодня\n"
        "🌅 <b>Завтра</b> - события на завтра\n"
        "📊 <b>Неделя</b> - события на ближайшие 7 дней\n"
        "📈 <b>Месяц</b> - события на ближайшие 30 дней"
    )

    await message.answer(text, reply_markup=get_calendar_menu_keyboard())


@router.message(F.text == "📅 Сегодня")
async def show_today_events(message: Message, session: AsyncSession):
    """
    Показать события на сегодня.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_calendar_events(message, session, "today")


@router.message(F.text == "🌅 Завтра")
async def show_tomorrow_events(message: Message, session: AsyncSession):
    """
    Показать события на завтра.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_calendar_events(message, session, "tomorrow")


@router.message(F.text == "📊 Неделя")
async def show_week_events(message: Message, session: AsyncSession):
    """
    Показать события на неделю.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_calendar_events(message, session, "week")


@router.message(F.text == "📈 Месяц")
async def show_month_events(message: Message, session: AsyncSession):
    """
    Показать события на месяц.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_calendar_events(message, session, "month")


async def show_calendar_events(
    message: Message, session: AsyncSession, period: str
):
    """
    Показать события за период.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
        period: Период (today, tomorrow, week, month)
    """
    calendar_service = CalendarService(session)

    # Получаем события в зависимости от периода
    if period == "today":
        events = await calendar_service.get_events_for_today()
    elif period == "tomorrow":
        events = await calendar_service.get_events_for_tomorrow()
    elif period == "week":
        events = await calendar_service.get_events_for_week()
    elif period == "month":
        events = await calendar_service.get_events_for_month()
    else:
        events = []

    # Форматируем сообщение
    period_name = calendar_service.get_period_name(period)
    text = calendar_service.format_calendar_message(events, period_name)

    # Если есть события, добавляем кнопки для просмотра
    if events:
        await message.answer(
            text,
            reply_markup=get_calendar_period_keyboard(events[:5], period)
        )
    else:
        await message.answer(text)


@router.callback_query(F.data.startswith("calendar_event:"))
async def show_calendar_event(callback: CallbackQuery, session: AsyncSession):
    """
    Показать событие из календаря.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    from src.database.repositories.user import UserRepository
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    from src.services.event_service import EventService
    from src.services.attendance_service import AttendanceService
    from src.bot.keyboards.events import get_event_detail_keyboard

    event_service = EventService(session)
    attendance_service = AttendanceService(session)

    event = await event_service.get_event_by_id(event_id)

    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return

    # Получаем статус пользователя
    user_status = await attendance_service.get_user_status(db_user.id, event_id)

    # Получаем статистику
    stats = await attendance_service.get_event_stats(event_id)

    # Получаем друзей
    friends_going = await attendance_service.get_friends_going(event_id, db_user.id)
    friends_maybe = await attendance_service.get_friends_maybe(event_id, db_user.id)

    # Форматируем сообщение
    text = event_service.format_event_message(event, show_full=True)

    # Добавляем статистику
    text += f"\n\n👥 <b>Участники:</b>\n"
    text += f"✅ Идут: {stats['going']}\n"
    text += f"❓ Возможно: {stats['maybe']}\n"

    # Добавляем информацию о друзьях
    if friends_going or friends_maybe:
        text += f"\n👫 <b>Ваши друзья:</b>\n"
        if friends_going:
            text += f"✅ Идут: {len(friends_going)}\n"
        if friends_maybe:
            text += f"❓ Возможно: {len(friends_maybe)}\n"

    # Добавляем статус пользователя
    if user_status:
        status_emoji = {"going": "✅", "maybe": "❓", "not_going": "❌"}
        status_text = {
            "going": "Вы идете",
            "maybe": "Вы возможно пойдете",
            "not_going": "Вы не идете",
        }
        text += f"\n{status_emoji[user_status]} <b>{status_text[user_status]}</b>"

    # Отправляем детальную информацию
    await callback.message.edit_text(
        text, reply_markup=get_event_detail_keyboard(event_id, user_status)
    )

    await callback.answer()


@router.callback_query(F.data == "calendar_back")
async def back_to_calendar(callback: CallbackQuery):
    """
    Вернуться к календарю.

    Args:
        callback: Callback query
    """
    await callback.message.delete()
    await cmd_calendar(callback.message)
    await callback.answer()
