"""Обработчики команд /start и /help."""
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu
from src.database.models.user import User
from src.database.repositories.user import UserRepository
from src.database.repositories.friendship import FriendshipRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, session: AsyncSession):
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        user: Пользователь из БД
        session: Сессия БД
    """
    # Проверяем есть ли параметр в команде (реферальный код или event_ID)
    command_args = message.text.split(maxsplit=1)
    param = command_args[1] if len(command_args) > 1 else None
    
    # Проверяем если это ссылка на событие
    if param and param.startswith("event_"):
        event_id = int(param.replace("event_", ""))
        
        # Показываем событие
        from src.services.event_service import EventService
        from src.bot.keyboards.events import get_event_detail_keyboard
        from src.services.attendance_service import AttendanceService
        
        event_service = EventService(session)
        attendance_service = AttendanceService(session)
        
        event = await event_service.get_event_by_id(event_id)
        
        if event:
            # Получаем статус пользователя
            user_status = await attendance_service.get_user_status(user.id, event_id)
            
            # Получаем статистику
            stats = await attendance_service.get_event_stats(event_id)
            
            # Получаем друзей
            friends_going = await attendance_service.get_friends_going(event_id, user.id)
            friends_maybe = await attendance_service.get_friends_maybe(event_id, user.id)
            
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
            
            await message.answer(
                text,
                reply_markup=get_event_detail_keyboard(event_id, user_status)
            )
            return
    
    # Если есть реферальный код и это не свой код
    referral_code = param
    if referral_code and referral_code != user.referral_code:
        user_repo = UserRepository(session)
        referrer = await user_repo.get_by_referral_code(referral_code)
        
        if referrer and referrer.id != user.id:
            # Автоматически добавляем в друзья
            friendship_repo = FriendshipRepository(session)
            
            # Проверяем что еще не друзья
            are_friends = await friendship_repo.are_friends(user.id, referrer.id)
            
            if not are_friends:
                # Создаем двустороннюю дружбу сразу (оба направления) со статусом accepted
                from src.database.models.friendship import Friendship
                
                # Направление 1: от нового пользователя к реферреру
                friendship1 = await friendship_repo.get_friendship(user.id, referrer.id)
                if not friendship1:
                    friendship1 = Friendship(
                        user_id=user.id,
                        friend_id=referrer.id,
                        status="accepted"
                    )
                    session.add(friendship1)
                elif friendship1.status != "accepted":
                    friendship1.status = "accepted"
                
                # Направление 2: от реферрера к новому пользователю
                friendship2 = await friendship_repo.get_friendship(referrer.id, user.id)
                if not friendship2:
                    friendship2 = Friendship(
                        user_id=referrer.id,
                        friend_id=user.id,
                        status="accepted"
                    )
                    session.add(friendship2)
                elif friendship2.status != "accepted":
                    friendship2.status = "accepted"
                
                await session.commit()
                
                # Отправляем уведомление
                referrer_name = referrer.first_name or referrer.username or "Пользователь"
                await message.answer(
                    f"🎉 Отлично! Вы автоматически добавлены в друзья с {referrer_name}!"
                )
                
                # Отправляем уведомление реферреру
                try:
                    new_user_name = user.first_name or user.username or "Новый пользователь"
                    await message.bot.send_message(
                        referrer.telegram_id,
                        f"🎉 {new_user_name} присоединился по вашей ссылке! Вы теперь друзья."
                    )
                except Exception:
                    pass  # Игнорируем ошибки отправки уведомления
    
    welcome_text = (
        f"👋 Привет, {user.first_name or 'друг'}!\n\n"
        f"Я бот для поиска IT и развлекательных мероприятий в Нижнем Новгороде.\n\n"
        f"🎯 Что я умею:\n"
        f"• 📅 Показывать актуальные события\n"
        f"• 📆 Формировать календарь на неделю/месяц\n"
        f"• 👥 Помогать находить друзей на мероприятиях\n"
        f"• 🔔 Отправлять уведомления о новых событиях\n\n"
        f"Выберите действие в меню ниже 👇"
    )

    await message.answer(welcome_text, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(lambda message: message.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """
    Обработчик команды /help.

    Args:
        message: Сообщение от пользователя
    """
    help_text = (
        "📖 <b>Справка по боту</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/events - Список событий\n"
        "/calendar - Календарь событий\n"
        "/friends - Управление друзьями\n"
        "/profile - Ваш профиль и настройки\n\n"
        "<b>Кнопки меню:</b>\n"
        "📅 События - Просмотр всех мероприятий\n"
        "📆 Календарь - События на неделю/месяц\n"
        "👥 Друзья - Список друзей и запросы\n"
        "👤 Профиль - Ваши данные и настройки\n\n"
        "<b>Категории событий:</b>\n"
        "💻 IT - Конференции, митапы, хакатоны\n"
        "🎉 Развлечения - Концерты, встречи, фестивали\n\n"
        "❓ Возникли вопросы? Напишите /help"
    )

    await message.answer(help_text, parse_mode="HTML")
