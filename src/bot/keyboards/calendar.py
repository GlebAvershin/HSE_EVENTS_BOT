"""Клавиатуры для работы с календарем."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_calendar_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру меню календаря.

    Returns:
        ReplyKeyboardMarkup: Клавиатура меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Сегодня"),
                KeyboardButton(text="🌅 Завтра"),
            ],
            [
                KeyboardButton(text="📊 Неделя"),
                KeyboardButton(text="📈 Месяц"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите период...",
    )
    return keyboard


def get_calendar_period_keyboard(
    events: list, period: str
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для просмотра событий календаря.

    Args:
        events: Список событий
        period: Период (today, tomorrow, week, month)

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    # Кнопки событий (максимум 5)
    for event in events[:5]:
        date_str = event.date_start.strftime("%d.%m %H:%M")
        button_text = f"{date_str} - {event.title[:25]}"
        if len(event.title) > 25:
            button_text += "..."

        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"calendar_event:{event.id}"
            )
        ])

    # Если событий больше 5, добавляем кнопку "Показать все"
    if len(events) > 5:
        buttons.append([
            InlineKeyboardButton(
                text=f"📋 Показать все ({len(events)})",
                callback_data=f"calendar_all:{period}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
