"""Главное меню бота."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Получить главное меню.

    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 События"),
                KeyboardButton(text="📆 Календарь"),
            ],
            [
                KeyboardButton(text="👥 Друзья"),
                KeyboardButton(text="👤 Профиль"),
            ],
            [
                KeyboardButton(text="ℹ️ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )
    return keyboard
