"""Обработчики для работы с друзьями."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.friends import (
    get_friends_menu_keyboard,
    get_friends_list_keyboard,
    get_friend_detail_keyboard,
    get_pending_requests_keyboard,
    get_request_actions_keyboard,
    get_sent_requests_keyboard,
)
from src.bot.keyboards.main_menu import get_main_menu
from src.services.friendship_service import FriendshipService
from src.database.repositories.user import UserRepository

router = Router()


class AddFriendStates(StatesGroup):
    """Состояния для добавления друга."""

    waiting_for_username = State()


async def get_user_db_id(telegram_id: int, session: AsyncSession) -> int | None:
    """
    Получить внутренний ID пользователя из БД по telegram_id.

    Args:
        telegram_id: Telegram ID пользователя
        session: Сессия БД

    Returns:
        int | None: Внутренний ID или None
    """
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(telegram_id)
    return db_user.id if db_user else None


@router.message(Command("friends"))
@router.message(F.text == "👥 Друзья")
async def cmd_friends(message: Message):
    """
    Обработчик команды /friends и кнопки "Друзья".

    Args:
        message: Сообщение от пользователя
    """
    text = (
        "👥 <b>Друзья</b>\n\n"
        "Управляйте своими друзьями:\n\n"
        "👥 <b>Мои друзья</b> - список ваших друзей\n"
        "📨 <b>Запросы</b> - входящие и исходящие запросы\n"
        "➕ <b>Добавить друга</b> - отправить запрос в друзья"
    )

    await message.answer(text, reply_markup=get_friends_menu_keyboard())


@router.message(F.text == "👥 Мои друзья")
async def show_friends_list(message: Message, session: AsyncSession):
    """
    Показать список друзей.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    user = message.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    friendship_service = FriendshipService(session)

    # Получаем список друзей
    friends = await friendship_service.get_friends_list(user_db_id)

    if not friends:
        await message.answer(
            "😔 У вас пока нет друзей.\n\n"
            "Используйте кнопку <b>➕ Добавить друга</b>, "
            "чтобы отправить запрос в друзья."
        )
        return

    text = f"👥 <b>Ваши друзья</b> ({len(friends)})\n\n"
    text += "Выберите друга для просмотра:"

    await message.answer(text, reply_markup=get_friends_list_keyboard(friends))


@router.message(F.text == "📨 Запросы")
async def show_requests_menu(message: Message, session: AsyncSession):
    """
    Показать меню запросов.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    user = message.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    friendship_service = FriendshipService(session)

    # Получаем входящие и исходящие запросы
    pending = await friendship_service.get_pending_requests(user_db_id)
    sent = await friendship_service.get_sent_requests(user_db_id)

    text = "📨 <b>Запросы в друзья</b>\n\n"
    text += f"📥 Входящие: {len(pending)}\n"
    text += f"📤 Исходящие: {len(sent)}\n\n"

    if pending:
        text += "Выберите запрос для ответа:"
        await message.answer(text, reply_markup=get_pending_requests_keyboard(pending))
    elif sent:
        text += "Ваши исходящие запросы:"
        await message.answer(text, reply_markup=get_sent_requests_keyboard(sent))
    else:
        text += "У вас нет активных запросов."
        await message.answer(text)


@router.message(F.text == "➕ Добавить друга")
async def add_friend_start(message: Message, state: FSMContext):
    """
    Начать процесс добавления друга.

    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    await message.answer(
        "➕ <b>Добавить друга</b>\n\n"
        "Введите username пользователя (без @):\n\n"
        "Например: <code>ivan_petrov</code>"
    )

    await state.set_state(AddFriendStates.waiting_for_username)


@router.message(F.text == "🔗 Пригласить друга")
async def invite_friend(message: Message, session: AsyncSession):
    """
    Показать реферальную ссылку для приглашения друзей.

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
    """
    user = message.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    # Получаем пользователя с реферальным кодом
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_id(user_db_id)
    
    if not db_user or not db_user.referral_code:
        await message.answer("❌ Ошибка: реферальный код не найден")
        return
    
    # Получаем информацию о боте
    bot = message.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    # Формируем реферальную ссылку
    referral_link = f"https://t.me/{bot_username}?start={db_user.referral_code}"
    
    text = (
        "🔗 <b>Пригласить друга</b>\n\n"
        "Отправьте эту ссылку своим друзьям:\n\n"
        f"<code>{referral_link}</code>\n\n"
        "Когда друг перейдет по ссылке и запустит бота, "
        "вы автоматически станете друзьями! 🎉\n\n"
        "💡 <b>Совет:</b> Нажмите на ссылку чтобы скопировать её"
    )
    
    await message.answer(text)


@router.message(AddFriendStates.waiting_for_username)
async def add_friend_process(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработать username для добавления друга.

    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
        session: Сессия БД
    """
    username = message.text.strip().lstrip("@")

    if not username:
        await message.answer("❌ Некорректный username. Попробуйте еще раз:")
        return

    user = message.from_user
    friendship_service = FriendshipService(session)

    # Получаем внутренний ID пользователя из БД
    from src.database.repositories.user import UserRepository
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_telegram_id(user.id)
    
    if not db_user:
        await message.answer("❌ Ошибка: пользователь не найден в системе")
        await state.clear()
        return

    # Отправляем запрос
    success, msg = await friendship_service.send_friend_request(db_user.id, username)

    await message.answer(msg)
    await state.clear()


@router.callback_query(F.data.startswith("friend_view:"))
async def show_friend_detail(callback: CallbackQuery, session: AsyncSession):
    """
    Показать детальную информацию о друге.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    friend_id = int(callback.data.split(":")[1])

    friendship_service = FriendshipService(session)

    # Получаем информацию о друге
    from src.database.repositories.user import UserRepository

    user_repo = UserRepository(session)
    friend = await user_repo.get_by_id(friend_id)

    if not friend:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    text = "👤 <b>Информация о друге</b>\n\n"
    text += f"Имя: {friendship_service.format_user_info(friend, show_username=True)}\n"

    await callback.message.edit_text(
        text, reply_markup=get_friend_detail_keyboard(friend_id)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("friend_remove:"))
async def remove_friend(callback: CallbackQuery, session: AsyncSession):
    """
    Удалить друга.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    friend_id = int(callback.data.split(":")[1])
    user = callback.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    friendship_service = FriendshipService(session)

    # Удаляем из друзей
    success, msg = await friendship_service.remove_friend(user_db_id, friend_id)

    await callback.answer(msg, show_alert=True)

    if success:
        await callback.message.delete()


@router.callback_query(F.data.startswith("request_view:"))
async def show_request_detail(callback: CallbackQuery, session: AsyncSession):
    """
    Показать детальную информацию о запросе.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    user_id = int(callback.data.split(":")[1])

    from src.database.repositories.user import UserRepository

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    friendship_service = FriendshipService(session)

    text = "📨 <b>Запрос в друзья</b>\n\n"
    text += f"От: {friendship_service.format_user_info(user, show_username=True)}\n\n"
    text += "Принять запрос?"

    await callback.message.edit_text(
        text, reply_markup=get_request_actions_keyboard(user_id)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("request_accept:"))
async def accept_request(callback: CallbackQuery, session: AsyncSession):
    """
    Принять запрос в друзья.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    friend_id = int(callback.data.split(":")[1])
    user = callback.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    friendship_service = FriendshipService(session)

    # Принимаем запрос
    success, msg = await friendship_service.accept_request(user_db_id, friend_id)

    await callback.answer(msg, show_alert=True)

    if success:
        await callback.message.delete()
        
        # Отправляем уведомление отправителю запроса
        from src.services.notification_service import NotificationService
        notification_service = NotificationService(session, callback.bot)
        await notification_service.notify_new_friend(friend_id, user_db_id)


@router.callback_query(F.data.startswith("request_reject:"))
async def reject_request(callback: CallbackQuery, session: AsyncSession):
    """
    Отклонить запрос в друзья.

    Args:
        callback: Callback query
        session: Сессия БД
    """
    friend_id = int(callback.data.split(":")[1])
    user = callback.from_user
    user_db_id = await get_user_db_id(user.id, session)
    
    if not user_db_id:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    friendship_service = FriendshipService(session)

    # Отклоняем запрос
    success, msg = await friendship_service.reject_request(user_db_id, friend_id)

    await callback.answer(msg, show_alert=True)

    if success:
        await callback.message.delete()


@router.callback_query(F.data == "friends_list")
async def back_to_friends_list(callback: CallbackQuery):
    """
    Вернуться к списку друзей.

    Args:
        callback: Callback query
    """
    await callback.message.delete()
    await cmd_friends(callback.message)
    await callback.answer()


@router.callback_query(F.data == "requests_list")
async def back_to_requests_list(callback: CallbackQuery):
    """
    Вернуться к списку запросов.

    Args:
        callback: Callback query
    """
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "friend_add")
async def add_friend_callback(callback: CallbackQuery, state: FSMContext):
    """
    Добавить друга через callback.

    Args:
        callback: Callback query
        state: Состояние FSM
    """
    await callback.message.delete()
    await add_friend_start(callback.message, state)
    await callback.answer()
