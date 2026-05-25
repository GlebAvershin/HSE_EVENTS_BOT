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
    events: list, period: str, page: int = 1, page_size: int = 8
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для просмотра событий календаря с пагинацией.

    Args:
        events: Полный список событий
        period: Период (today, tomorrow, week, month)
        page: Текущая страница
        page_size: Событий на странице

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []
    
    total = len(events)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_events = events[start:end]

    # Кнопки событий
    for event in page_events:
        date_str = event.date_start.strftime("%d.%m %H:%M")
        category_emoji = "💻" if event.category == "it" else "🎉"
        title_short = event.title[:30] + ("..." if len(event.title) > 30 else "")
        button_text = f"{category_emoji} {date_str} — {title_short}"

        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"calendar_event:{event.id}"
            )
        ])

    # Пагинация
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(
                text="◀️",
                callback_data=f"calendar_page:{period}:{page - 1}"
            ))
        nav_row.append(InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        ))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(
                text="▶️",
                callback_data=f"calendar_page:{period}:{page + 1}"
            ))
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
