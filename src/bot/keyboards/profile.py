"""Клавиатуры для работы с профилем."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру меню профиля.

    Returns:
        ReplyKeyboardMarkup: Клавиатура меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )
    return keyboard


def get_settings_keyboard(settings) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру настроек уведомлений.

    Args:
        settings: Настройки пользователя

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    # Эмодзи для вкл/выкл
    friend_emoji = "✅" if settings.notify_friend_going else "❌"
    events_emoji = "✅" if settings.notify_new_events else "❌"
    reminder_emoji = "✅" if settings.notify_event_reminder else "❌"
    
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{friend_emoji} Друзья на событиях",
                callback_data="toggle_friend_going"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{events_emoji} Новые события",
                callback_data="toggle_new_events"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{reminder_emoji} Напоминания о событиях",
                callback_data="toggle_event_reminder"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад к профилю",
                callback_data="back_to_profile"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
