"""Обработчики для работы с событиями."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.events import (
    get_events_category_keyboard,
    get_events_list_keyboard,
    get_event_detail_keyboard,
)
from src.bot.keyboards.main_menu import get_main_menu
from src.services.event_service import EventService
from src.services.attendance_service import AttendanceService
from src.database.repositories.user import UserRepository

router = Router()


@router.message(Command("events"))
@router.message(F.text == "📅 События")
async def cmd_events(message: Message):
    """
    Обработчик команды /events и кнопки "События".

    Args:
        message: Сообщение от пользователя
    """
    text = (
        "📅 <b>События</b>\n\n"
        "Выберите категорию событий, которые вас интересуют:\n\n"
        "💻 <b>IT-мероприятия</b> - конференции, митапы, хакатоны\n"
        "🎉 <b>Развлечения</b> - концерты, встречи, фестивали\n"
        "📋 <b>Все события</b> - все предстоящие мероприятия"
    )

    await message.answer(text, reply_markup=get_events_category_keyboard())


@router.message(F.text == "💻 IT-мероприятия")
async def show_it_events(message: Message, session: AsyncSession):
    """
    Показать IT-мероприятия.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_events_by_category(message, session, "it")


@router.message(F.text == "🎉 Развлечения")
async def show_entertainment_events(message: Message, session: AsyncSession):
    """
    Показать развлекательные мероприятия.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_events_by_category(message, session, "entertainment")


@router.message(F.text == "📋 Все события")
async def show_all_events(message: Message, session: AsyncSession):
    """
    Показать все события.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    await show_events_by_category(message, session, None)


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message):
    """
    Вернуться в главное меню.

    Args:
        message: Сообщение от пользователя
    """
    await message.answer(
        "Главное меню:", reply_markup=get_main_menu()
    )


async def show_events_by_category(
    message: Message, session: AsyncSession, category: str | None
):
    """
    Показать события по категории.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
        category: Категория событий
    """
    event_service = EventService(session)

    # Получаем события
    events, total = await event_service.get_events_list(category=category, page=1, page_size=5)

    if not events:
        category_name = event_service.get_category_name(category or "all")
        await message.answer(
            f"😔 К сожалению, пока нет предстоящих событий в категории <b>{category_name}</b>.\n\n"
            f"Попробуйте выбрать другую категорию или зайдите позже!"
        )
        return

    # Формируем сообщение
    category_name = event_service.get_category_name(category or "all")
    text = f"📋 <b>{category_name}</b>\n\n"
    text += f"Найдено событий: {total}\n\n"
    text += "Выберите событие для подробной информации:"

    # Вычисляем количество страниц
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    # Отправляем список
    await message.answer(
        text,
        reply_markup=get_events_list_keyboard(
            events=events, page=1, total_pages=total_pages, category=category
        ),
    )


@router.callback_query(F.data.startswith("event_view:"))
async def show_event_detail(callback: CallbackQuery, session: AsyncSession):
    """
    Показать детальную информацию о событии.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

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


@router.callback_query(F.data.startswith("events_page:"))
async def show_events_page(callback: CallbackQuery, session: AsyncSession):
    """
    Показать страницу со списком событий.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    parts = callback.data.split(":")
    page = int(parts[1])
    category = parts[2] if parts[2] != "all" else None

    event_service = EventService(session)

    # Получаем события
    events, total = await event_service.get_events_list(
        category=category, page=page, page_size=5
    )

    if not events:
        await callback.answer("❌ События не найдены", show_alert=True)
        return

    # Формируем сообщение
    category_name = event_service.get_category_name(category or "all")
    text = f"📋 <b>{category_name}</b>\n\n"
    text += f"Найдено событий: {total}\n\n"
    text += "Выберите событие для подробной информации:"

    # Вычисляем количество страниц
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    # Обновляем сообщение
    await callback.message.edit_text(
        text,
        reply_markup=get_events_list_keyboard(
            events=events, page=page, total_pages=total_pages, category=category
        ),
    )

    await callback.answer()


@router.callback_query(F.data == "events_list")
async def back_to_events_list(callback: CallbackQuery):
    """
    Вернуться к списку событий.

    Args:
        callback: Callback query
    """
    await callback.message.delete()
    await cmd_events(callback.message)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """
    Пустой callback (для кнопок-индикаторов).

    Args:
        callback: Callback query
    """
    await callback.answer()


@router.callback_query(F.data.startswith("event_going:"))
async def event_going(callback: CallbackQuery, session: AsyncSession):
    """
    Отметить "Я пойду" на событие.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Устанавливаем статус
    attendance_service = AttendanceService(session)
    success, message = await attendance_service.set_going(db_user.id, event_id)

    if success:
        # Сначала показываем уведомление
        await callback.answer(message, show_alert=False)
        # Потом обновляем сообщение с новой информацией
        await update_event_detail(callback, session, event_id, db_user.id)
        
        # Отправляем уведомления друзьям
        from src.services.notification_service import NotificationService
        notification_service = NotificationService(session, callback.bot)
        await notification_service.notify_friends_about_attendance(
            db_user.id, event_id, "going"
        )
    else:
        await callback.answer(message, show_alert=True)


@router.callback_query(F.data.startswith("event_maybe:"))
async def event_maybe(callback: CallbackQuery, session: AsyncSession):
    """
    Отметить "Возможно" на событие.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Устанавливаем статус
    attendance_service = AttendanceService(session)
    success, message = await attendance_service.set_maybe(db_user.id, event_id)

    if success:
        # Сначала показываем уведомление
        await callback.answer(message, show_alert=False)
        # Потом обновляем сообщение с новой информацией
        await update_event_detail(callback, session, event_id, db_user.id)
        
        # Отправляем уведомления друзьям
        from src.services.notification_service import NotificationService
        notification_service = NotificationService(session, callback.bot)
        await notification_service.notify_friends_about_attendance(
            db_user.id, event_id, "maybe"
        )
    else:
        await callback.answer(message, show_alert=True)


@router.callback_query(F.data.startswith("event_friends:"))
async def show_event_friends(callback: CallbackQuery, session: AsyncSession):
    """
    Показать друзей на событии.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Получаем информацию о событии
    event_service = EventService(session)
    event = await event_service.get_event_by_id(event_id)

    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return

    # Получаем друзей
    attendance_service = AttendanceService(session)
    friends_going = await attendance_service.get_friends_going(event_id, db_user.id)
    friends_maybe = await attendance_service.get_friends_maybe(event_id, db_user.id)

    # Формируем сообщение
    text = f"👥 <b>Друзья на событии</b>\n\n"
    text += f"📅 {event.title}\n\n"

    if friends_going:
        text += f"✅ <b>Идут ({len(friends_going)}):</b>\n"
        text += attendance_service.format_friends_list(friends_going)
        text += "\n\n"

    if friends_maybe:
        text += f"❓ <b>Возможно ({len(friends_maybe)}):</b>\n"
        text += attendance_service.format_friends_list(friends_maybe)
        text += "\n\n"

    if not friends_going and not friends_maybe:
        text += "😔 Никто из ваших друзей пока не отметился на это событие.\n\n"
        text += "Пригласите их!"

    await callback.answer()
    await callback.message.answer(text)


async def update_event_detail(
    callback: CallbackQuery, session: AsyncSession, event_id: int, user_id: int
):
    """
    Обновить детальную информацию о событии.

    Args:
        callback: Callback query
        session: Сессия БД
        event_id: ID события
        user_id: ID пользователя
    """
    event_service = EventService(session)
    attendance_service = AttendanceService(session)

    event = await event_service.get_event_by_id(event_id)
    if not event:
        return

    # Получаем статус пользователя
    user_status = await attendance_service.get_user_status(user_id, event_id)

    # Получаем статистику
    stats = await attendance_service.get_event_stats(event_id)

    # Получаем друзей
    friends_going = await attendance_service.get_friends_going(event_id, user_id)
    friends_maybe = await attendance_service.get_friends_maybe(event_id, user_id)

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

    # Обновляем клавиатуру с учетом статуса
    await callback.message.edit_text(
        text, reply_markup=get_event_detail_keyboard(event_id, user_status)
    )


@router.callback_query(F.data.startswith("event_invite:"))
async def invite_friend_to_event(callback: CallbackQuery, session: AsyncSession):
    """
    Пригласить друга на событие.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])

    event_service = EventService(session)
    event = await event_service.get_event_by_id(event_id)

    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return

    # Получаем информацию о боте
    bot = callback.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Формируем ссылку для приглашения (deep link)
    invite_link = f"https://t.me/{bot_username}?start=event_{event_id}"

    # Формируем текст для share
    share_text = (
        f"🎉 Привет! Я иду на событие:\n\n"
        f"📅 {event.title}\n"
        f"📆 {event.date_start.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 {event.location}\n\n"
        f"Присоединяйся! 👇"
    )

    # Создаем share-ссылку
    from urllib.parse import quote
    share_url = f"https://t.me/share/url?url={quote(invite_link)}&text={quote(share_text)}"

    # Создаем клавиатуру с кнопкой share
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться в Telegram", url=share_url)],
        [InlineKeyboardButton(text="🔗 Скопировать ссылку", callback_data=f"event_copy_link:{event_id}")],
        [InlineKeyboardButton(text="🔙 Назад к событию", callback_data=f"event_view:{event_id}")]
    ])

    text = (
        f"📤 <b>Пригласить друга на событие</b>\n\n"
        f"📅 {event.title}\n\n"
        f"Вы можете:\n"
        f"1️⃣ Нажать кнопку ниже чтобы поделиться в Telegram\n"
        f"2️⃣ Скопировать ссылку и отправить другу:\n\n"
        f"<code>{invite_link}</code>\n\n"
        f"Когда друг перейдет по ссылке, он увидит это событие!"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("event_copy_link:"))
async def copy_event_link(callback: CallbackQuery, session: AsyncSession):
    """
    Скопировать ссылку на событие.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])

    # Получаем информацию о боте
    bot = callback.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Формируем ссылку
    invite_link = f"https://t.me/{bot_username}?start=event_{event_id}"

    await callback.answer(
        f"✅ Ссылка скопирована!\n{invite_link}",
        show_alert=True
    )


@router.callback_query(F.data.startswith("notif_going:"))
async def notif_going(callback: CallbackQuery, session: AsyncSession):
    """
    Отметить "Я пойду" из уведомления.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Устанавливаем статус
    attendance_service = AttendanceService(session)
    success, message = await attendance_service.set_going(db_user.id, event_id)

    if success:
        await callback.answer(message, show_alert=False)
        
        # Обновляем сообщение уведомления
        event_service = EventService(session)
        event = await event_service.get_event_by_id(event_id)
        
        if event:
            text = callback.message.text + f"\n\n✅ <b>Вы отметились: Я пойду</b>"
            
            # Убираем кнопки после отметки
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👁 Посмотреть событие",
                        callback_data=f"event_view:{event_id}"
                    )
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        
        # Отправляем уведомления друзьям
        from src.services.notification_service import NotificationService
        notification_service = NotificationService(session, callback.bot)
        await notification_service.notify_friends_about_attendance(
            db_user.id, event_id, "going"
        )
    else:
        await callback.answer(message, show_alert=True)


@router.callback_query(F.data.startswith("notif_maybe:"))
async def notif_maybe(callback: CallbackQuery, session: AsyncSession):
    """
    Отметить "Возможно" из уведомления.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Устанавливаем статус
    attendance_service = AttendanceService(session)
    success, message = await attendance_service.set_maybe(db_user.id, event_id)

    if success:
        await callback.answer(message, show_alert=False)
        
        # Обновляем сообщение уведомления
        event_service = EventService(session)
        event = await event_service.get_event_by_id(event_id)
        
        if event:
            text = callback.message.text + f"\n\n❓ <b>Вы отметились: Возможно</b>"
            
            # Убираем кнопки после отметки
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👁 Посмотреть событие",
                        callback_data=f"event_view:{event_id}"
                    )
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        
        # Отправляем уведомления друзьям
        from src.services.notification_service import NotificationService
        notification_service = NotificationService(session, callback.bot)
        await notification_service.notify_friends_about_attendance(
            db_user.id, event_id, "maybe"
        )
    else:
        await callback.answer(message, show_alert=True)


@router.callback_query(F.data.startswith("event_cancel:"))
async def event_cancel(callback: CallbackQuery, session: AsyncSession):
    """
    Отменить запись на событие.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])
    user = callback.from_user

    # Получаем внутренний ID пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Удаляем запись
    attendance_service = AttendanceService(session)
    success, message = await attendance_service.remove_attendance(db_user.id, event_id)

    if success:
        # Сначала показываем уведомление
        await callback.answer("🗑 Запись отменена", show_alert=False)
        # Потом обновляем сообщение с новой информацией
        await update_event_detail(callback, session, event_id, db_user.id)
    else:
        await callback.answer(message, show_alert=True)
