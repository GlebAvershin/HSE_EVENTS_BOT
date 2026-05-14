"""Обработчики для работы с событиями."""
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.events import (
    get_events_category_keyboard,
    get_events_list_keyboard,
    get_event_detail_keyboard,
    get_events_filter_keyboard,
    get_rating_keyboard,
    get_skip_comment_keyboard,
    get_comments_keyboard,
)
from src.bot.keyboards.main_menu import get_main_menu
from src.services.event_service import EventService
from src.services.attendance_service import AttendanceService
from src.database.repositories.user import UserRepository
from src.database.repositories.event import EventRepository
from src.database.models.review import EventReview
from src.database.models.comment import EventComment

router = Router()


class SearchEventsStates(StatesGroup):
    """Состояния для поиска событий."""

    waiting_for_query = State()


class ReviewStates(StatesGroup):
    """Состояния для оставления отзыва."""

    waiting_for_comment = State()


class CommentStates(StatesGroup):
    """Состояния для написания комментария."""

    waiting_for_text = State()


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
async def back_to_main_menu(message: Message, state: FSMContext):
    """
    Вернуться в главное меню.

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
    """
    await state.clear()
    await message.answer(
        "Главное меню:", reply_markup=get_main_menu()
    )


@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    """
    Начать поиск событий — переход в FSM состояние ожидания запроса.

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
    """
    await state.set_state(SearchEventsStates.waiting_for_query)
    await message.answer(
        "🔍 <b>Поиск событий</b>\n\n"
        "Введите текст для поиска (название или описание события):\n\n"
        "Для отмены нажмите «🔙 Главное меню»"
    )


@router.message(SearchEventsStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработать поисковый запрос пользователя.

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
        session: Сессия БД
    """
    search_text = message.text.strip()

    if not search_text:
        await message.answer("❌ Введите текст для поиска.")
        return

    await state.clear()

    event_service = EventService(session)
    events = await event_service.search_events(search_text=search_text, category=None)

    if not events:
        await message.answer(
            f"😔 По запросу «{search_text}» ничего не найдено.\n\n"
            "Попробуйте другой запрос или выберите категорию.",
            reply_markup=get_events_category_keyboard(),
        )
        return

    total = len(events)
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    text = f"🔍 <b>Результаты поиска:</b> «{search_text}»\n\n"
    text += f"Найдено событий: {total}\n\n"
    text += "Выберите событие для подробной информации:"

    await message.answer(
        text,
        reply_markup=get_events_list_keyboard(
            events=events[:page_size], page=1, total_pages=total_pages, category=None
        ),
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
    text += "Фильтры:"

    # Отправляем фильтры
    await message.answer(text, reply_markup=get_events_filter_keyboard(category))

    # Вычисляем количество страниц
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    # Отправляем список
    await message.answer(
        "Выберите событие для подробной информации:",
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

    # Добавляем средний рейтинг
    rating_text = await _get_event_rating_text(session, event_id)
    if rating_text:
        text += f"\n\n{rating_text}"

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

    # Определяем, показывать ли кнопку "Оценить"
    show_rate = (
        event.date_start < datetime.utcnow() and user_status == "going"
    )

    # Отправляем детальную информацию
    await callback.message.edit_text(
        text, reply_markup=get_event_detail_keyboard(event_id, user_status, show_rate=show_rate)
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


@router.callback_query(F.data.startswith("events_filter:"))
async def handle_events_filter(callback: CallbackQuery, session: AsyncSession):
    """
    Обработать фильтр событий (неделя, месяц, популярные, все).

    Args:
        callback: Callback query
        session: Сессия БД
    """
    parts = callback.data.split(":")
    filter_type = parts[1]
    category = parts[2] if parts[2] != "all" else None

    event_repo = EventRepository(session)
    event_service = EventService(session)
    events: list = []
    filter_label = ""

    now = datetime.utcnow()

    if filter_type == "week":
        end_date = now + timedelta(days=7)
        events = await event_repo.get_events_by_date_range(
            start_date=now, end_date=end_date, category=category
        )
        filter_label = "📅 На этой неделе"

    elif filter_type == "month":
        end_date = now + timedelta(days=30)
        events = await event_repo.get_events_by_date_range(
            start_date=now, end_date=end_date, category=category
        )
        filter_label = "📅 В этом месяце"

    elif filter_type == "popular":
        events = await event_repo.get_popular_events(category=category, limit=10)
        filter_label = "🔥 Популярные"

    elif filter_type == "online":
        from sqlalchemy import select, and_, or_
        from src.database.models.event import Event
        query = select(Event).where(
            and_(
                Event.is_published == True,
                Event.date_start >= now,
                or_(
                    Event.location.ilike("%онлайн%"),
                    Event.location.ilike("%online%"),
                ),
            )
        )
        if category:
            query = query.where(Event.category == category)
        query = query.order_by(Event.date_start)
        result = await session.execute(query)
        events = list(result.scalars().all())
        filter_label = "🌐 Онлайн"

    elif filter_type == "offline":
        from sqlalchemy import select, and_, not_, or_
        from src.database.models.event import Event
        query = select(Event).where(
            and_(
                Event.is_published == True,
                Event.date_start >= now,
                not_(
                    or_(
                        Event.location.ilike("%онлайн%"),
                        Event.location.ilike("%online%"),
                    )
                ),
            )
        )
        if category:
            query = query.where(Event.category == category)
        query = query.order_by(Event.date_start)
        result = await session.execute(query)
        events = list(result.scalars().all())
        filter_label = "📍 Офлайн"

    else:  # "all"
        events_list, _ = await event_service.get_events_list(category=category, page=1, page_size=5)
        events = events_list
        filter_label = "📋 Все"

    if not events:
        await callback.answer("😔 Событий не найдено", show_alert=True)
        return

    total = len(events)
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    category_name = event_service.get_category_name(category or "all")
    text = f"📋 <b>{category_name}</b> — {filter_label}\n\n"
    text += f"Найдено событий: {total}\n\n"
    text += "Выберите событие для подробной информации:"

    await callback.message.edit_text(
        text,
        reply_markup=get_events_list_keyboard(
            events=events[:page_size], page=1, total_pages=total_pages, category=category
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

    # Добавляем средний рейтинг
    rating_text = await _get_event_rating_text(session, event_id)
    if rating_text:
        text += f"\n\n{rating_text}"

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

    # Определяем, показывать ли кнопку "Оценить"
    show_rate = (
        event.date_start < datetime.utcnow() and user_status == "going"
    )

    # Обновляем клавиатуру с учетом статуса
    await callback.message.edit_text(
        text, reply_markup=get_event_detail_keyboard(event_id, user_status, show_rate=show_rate)
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


# ==================== Вспомогательные функции ====================


async def _get_event_rating_text(session: AsyncSession, event_id: int) -> str | None:
    """
    Получить текст со средним рейтингом события.

    Args:
        session: Сессия БД
        event_id: ID события

    Returns:
        Строка вида "⭐ 4.2 (5 отзывов)" или None если отзывов нет
    """
    result = await session.execute(
        select(
            func.avg(EventReview.rating),
            func.count(EventReview.id),
        ).where(EventReview.event_id == event_id)
    )
    row = result.one()
    avg_rating, count = row[0], row[1]

    if not count:
        return None

    avg_rating = round(float(avg_rating), 1)

    # Склонение слова "отзыв"
    if count % 10 == 1 and count % 100 != 11:
        word = "отзыв"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        word = "отзыва"
    else:
        word = "отзывов"

    return f"⭐ {avg_rating} ({count} {word})"


# ==================== Обработчики отзывов (Reviews) ====================


@router.callback_query(F.data.startswith("event_rate:"))
async def event_rate(callback: CallbackQuery, session: AsyncSession):
    """
    Показать клавиатуру выбора рейтинга.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])

    # Проверяем, что пользователь существует
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Проверяем, не оставлял ли уже отзыв
    existing = await session.execute(
        select(EventReview).where(
            EventReview.user_id == db_user.id,
            EventReview.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none():
        await callback.answer("⭐ Вы уже оценили это событие", show_alert=True)
        return

    text = "⭐ <b>Оцените событие</b>\n\nВыберите оценку от 1 до 5:"

    await callback.message.edit_text(text, reply_markup=get_rating_keyboard(event_id))
    await callback.answer()


@router.callback_query(F.data.startswith("event_rate_submit:"))
async def event_rate_submit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Сохранить рейтинг и предложить оставить комментарий.

    Args:
        callback: Callback query
        state: FSM контекст
        session: Сессия БД
    """
    parts = callback.data.split(":")
    event_id = int(parts[1])
    rating = int(parts[2])

    # Проверяем валидность рейтинга
    if rating < 1 or rating > 5:
        await callback.answer("❌ Некорректная оценка", show_alert=True)
        return

    # Получаем пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Сохраняем рейтинг в FSM state (комментарий добавим позже)
    await state.set_state(ReviewStates.waiting_for_comment)
    await state.update_data(event_id=event_id, rating=rating, user_id=db_user.id)

    text = (
        f"⭐ Вы поставили оценку: {'⭐' * rating}\n\n"
        f"Хотите оставить комментарий к отзыву?\n"
        f"Напишите текст или нажмите «Пропустить»."
    )

    await callback.message.edit_text(text, reply_markup=get_skip_comment_keyboard())
    await callback.answer()


@router.callback_query(F.data == "review_skip_comment", ReviewStates.waiting_for_comment)
async def review_skip_comment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Пропустить комментарий к отзыву и сохранить только рейтинг.

    Args:
        callback: Callback query
        state: FSM контекст
        session: Сессия БД
    """
    data = await state.get_data()
    event_id = data["event_id"]
    rating = data["rating"]
    user_id = data["user_id"]

    # Сохраняем отзыв без комментария
    review = EventReview(
        user_id=user_id,
        event_id=event_id,
        rating=rating,
        comment=None,
    )
    session.add(review)
    await session.commit()

    await state.clear()

    await callback.message.edit_text(
        f"✅ Спасибо за оценку! Вы поставили {'⭐' * rating}"
    )
    await callback.answer()


@router.message(ReviewStates.waiting_for_comment)
async def review_save_comment(message: Message, state: FSMContext, session: AsyncSession):
    """
    Сохранить отзыв с комментарием.

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
        session: Сессия БД
    """
    data = await state.get_data()
    event_id = data["event_id"]
    rating = data["rating"]
    user_id = data["user_id"]

    comment_text = message.text.strip() if message.text else None

    # Сохраняем отзыв с комментарием
    review = EventReview(
        user_id=user_id,
        event_id=event_id,
        rating=rating,
        comment=comment_text,
    )
    session.add(review)
    await session.commit()

    await state.clear()

    await message.answer(
        f"✅ Спасибо за отзыв! Вы поставили {'⭐' * rating}\n"
        f"💬 Ваш комментарий сохранён."
    )


# ==================== Обработчики комментариев (Comments) ====================


@router.callback_query(F.data.startswith("event_discuss:"))
async def event_discuss(callback: CallbackQuery, session: AsyncSession):
    """
    Показать последние комментарии к событию.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])

    # Получаем событие
    event_service = EventService(session)
    event = await event_service.get_event_by_id(event_id)

    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return

    # Получаем последние 5 комментариев
    from src.database.models.user import User

    result = await session.execute(
        select(EventComment, User)
        .join(User, EventComment.user_id == User.id)
        .where(EventComment.event_id == event_id)
        .order_by(EventComment.created_at.desc())
        .limit(5)
    )
    comments = result.all()

    # Считаем общее количество комментариев
    count_result = await session.execute(
        select(func.count(EventComment.id)).where(EventComment.event_id == event_id)
    )
    total_comments = count_result.scalar() or 0

    # Склонение слова "комментарий"
    if total_comments % 10 == 1 and total_comments % 100 != 11:
        word = "комментарий"
    elif total_comments % 10 in (2, 3, 4) and total_comments % 100 not in (12, 13, 14):
        word = "комментария"
    else:
        word = "комментариев"

    text = f"💬 <b>Обсуждение</b> ({total_comments} {word})\n\n"

    if comments:
        # Выводим в хронологическом порядке (от старых к новым)
        for comment_row in reversed(comments):
            comment = comment_row[0]
            user = comment_row[1]
            username_str = f"@{user.username}" if user.username else ""
            name = user.first_name or "Пользователь"
            date_str = comment.created_at.strftime("%d.%m.%Y %H:%M")
            text += f"👤 {name} ({username_str}): {comment.text}\n"
            text += f"   {date_str}\n\n"
    else:
        text += "Пока нет комментариев. Будьте первым!\n"

    await callback.message.edit_text(text, reply_markup=get_comments_keyboard(event_id))
    await callback.answer()


@router.callback_query(F.data.startswith("event_comment:"))
async def event_comment_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Начать написание комментария — переход в FSM состояние.

    Args:
        callback: Callback query
        state: FSM контекст
        session: Сессия БД
    """
    event_id = int(callback.data.split(":")[1])

    # Получаем пользователя
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if not db_user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    await state.set_state(CommentStates.waiting_for_text)
    await state.update_data(event_id=event_id, user_id=db_user.id)

    await callback.message.edit_text(
        "✍️ <b>Напишите ваш комментарий:</b>\n\n"
        "Отправьте текст сообщения."
    )
    await callback.answer()


@router.message(CommentStates.waiting_for_text)
async def comment_save_text(message: Message, state: FSMContext, session: AsyncSession):
    """
    Сохранить комментарий к событию.

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
        session: Сессия БД
    """
    data = await state.get_data()
    event_id = data["event_id"]
    user_id = data["user_id"]

    comment_text = message.text.strip() if message.text else ""

    if not comment_text:
        await message.answer("❌ Комментарий не может быть пустым. Попробуйте ещё раз.")
        return

    # Сохраняем комментарий
    comment = EventComment(
        user_id=user_id,
        event_id=event_id,
        text=comment_text,
    )
    session.add(comment)
    await session.commit()

    await state.clear()

    await message.answer("✅ Ваш комментарий опубликован!")
