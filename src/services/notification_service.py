"""Сервис для работы с уведомлениями."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from src.database.repositories.user import UserRepository
from src.database.repositories.event import EventRepository
from src.database.repositories.friendship import FriendshipRepository
from src.database.repositories.attendance import AttendanceRepository


class NotificationService:
    """Сервис для работы с уведомлениями."""

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
            bot: Экземпляр бота
        """
        self.session = session
        self.bot = bot
        self.user_repo = UserRepository(session)
        self.event_repo = EventRepository(session)
        self.friendship_repo = FriendshipRepository(session)
        self.attendance_repo = AttendanceRepository(session)

    async def notify_friends_about_attendance(
        self, user_id: int, event_id: int, status: str
    ):
        """
        Уведомить друзей о том что пользователь отметился на событие.

        Args:
            user_id: ID пользователя
            event_id: ID события
            status: Статус ('going' или 'maybe')
        """
        # Получаем пользователя
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return

        # Получаем событие
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            return

        # Получаем друзей
        friends = await self.friendship_repo.get_friends(user_id)

        # Формируем сообщение
        user_name = user.first_name or user.username or "Ваш друг"
        status_text = "идет" if status == "going" else "возможно пойдет"
        
        base_text = (
            f"👥 <b>Друг на событии!</b>\n\n"
            f"{user_name} {status_text} на событие:\n\n"
            f"📅 {event.title}\n"
            f"📆 {event.date_start.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {event.location}"
        )

        # Отправляем уведомления друзьям
        for friend in friends:
            try:
                # Проверяем настройки уведомлений друга
                from src.database.models.user_settings import UserSettings
                from sqlalchemy import select
                
                result = await self.session.execute(
                    select(UserSettings).where(UserSettings.user_id == friend.id)
                )
                friend_settings = result.scalar_one_or_none()
                
                # Если уведомления о друзьях выключены - пропускаем
                if friend_settings and not friend_settings.notify_friend_going:
                    continue
                
                # Проверяем, не отметился ли уже друг на это событие
                friend_attendance = await self.attendance_repo.get_attendance(
                    friend.id, event_id
                )
                
                # Если друг уже отметился, отправляем уведомление без кнопок
                if friend_attendance:
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    
                    # Меняем текст - друг уже записан
                    text = base_text + "\n\n✅ <b>Вы тоже идете на это событие!</b>"
                    
                    # Показываем только кнопку "Посмотреть событие"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="👁 Посмотреть событие",
                                callback_data=f"event_view:{event_id}"
                            )
                        ]
                    ])
                    
                    await self.bot.send_message(
                        friend.telegram_id,
                        text,
                        reply_markup=keyboard
                    )
                else:
                    # Друг еще не отметился - показываем кнопки для записи
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    
                    text = base_text + "\n\nПрисоединяйтесь!"
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ Я тоже пойду",
                                callback_data=f"notif_going:{event_id}"
                            ),
                            InlineKeyboardButton(
                                text="❓ Возможно",
                                callback_data=f"notif_maybe:{event_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="👁 Посмотреть событие",
                                callback_data=f"event_view:{event_id}"
                            )
                        ]
                    ])
                    
                    await self.bot.send_message(
                        friend.telegram_id,
                        text,
                        reply_markup=keyboard
                    )
            except Exception as e:
                # Игнорируем ошибки (пользователь заблокировал бота и т.д.)
                pass

    async def notify_event_reminder(self, event_id: int, hours_before: int = 24):
        """
        Отправить напоминание о событии всем участникам.

        Args:
            event_id: ID события
            hours_before: За сколько часов до события
        """
        # Получаем событие
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            return

        # Получаем участников со статусом "going"
        attendees = await self.attendance_repo.get_event_attendees(
            event_id, status="going"
        )

        # Формируем сообщение
        time_text = "завтра" if hours_before == 24 else f"через {hours_before} часов"
        
        text = (
            f"⏰ <b>Напоминание о событии!</b>\n\n"
            f"Событие начнется {time_text}:\n\n"
            f"📅 {event.title}\n"
            f"📆 {event.date_start.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {event.location}\n"
        )
        
        if event.address:
            text += f"🗺 {event.address}\n"
        
        text += f"\nНе опоздайте! 🎉"

        # Отправляем напоминания
        for attendee in attendees:
            try:
                await self.bot.send_message(attendee.telegram_id, text)
            except Exception:
                pass

    async def notify_new_friend(self, user_id: int, friend_id: int):
        """
        Уведомить пользователя о новом друге.

        Args:
            user_id: ID пользователя
            friend_id: ID нового друга
        """
        user = await self.user_repo.get_by_id(user_id)
        friend = await self.user_repo.get_by_id(friend_id)
        
        if not user or not friend:
            return

        friend_name = friend.first_name or friend.username or "Пользователь"
        
        text = (
            f"🎉 <b>Новый друг!</b>\n\n"
            f"{friend_name} принял ваш запрос в друзья!\n\n"
            f"Теперь вы можете видеть на каких событиях он будет."
        )

        try:
            await self.bot.send_message(user.telegram_id, text)
        except Exception:
            pass

    def format_user_name(self, user) -> str:
        """
        Форматировать имя пользователя.

        Args:
            user: Пользователь

        Returns:
            str: Отформатированное имя
        """
        if user.first_name:
            return user.first_name
        elif user.username:
            return f"@{user.username}"
        else:
            return "Пользователь"
