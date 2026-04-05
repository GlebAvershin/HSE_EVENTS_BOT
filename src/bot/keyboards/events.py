"""Клавиатуры для работы с событиями."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_events_category_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру выбора категории событий.

    Returns:
        ReplyKeyboardMarkup: Клавиатура категорий
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💻 IT-мероприятия"),
                KeyboardButton(text="🎉 Развлечения"),
            ],
            [
                KeyboardButton(text="📋 Все события"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите категорию...",
    )
    return keyboard


def get_event_detail_keyboard(event_id: int, user_status: str | None = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для детального просмотра события.

    Args:
        event_id: ID события
        user_status: Статус пользователя ('going', 'maybe', None)

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    # Кнопки посещения (меняются в зависимости от статуса)
    if user_status == "going":
        buttons.append([
            InlineKeyboardButton(text="✅ Вы идете", callback_data="noop"),
            InlineKeyboardButton(text="❓ Возможно", callback_data=f"event_maybe:{event_id}"),
        ])
        # Кнопка отмены
        buttons.append([
            InlineKeyboardButton(text="🗑 Отменить запись", callback_data=f"event_cancel:{event_id}")
        ])
    elif user_status == "maybe":
        buttons.append([
            InlineKeyboardButton(text="✅ Я пойду", callback_data=f"event_going:{event_id}"),
            InlineKeyboardButton(text="❓ Вы возможно пойдете", callback_data="noop"),
        ])
        # Кнопка отмены
        buttons.append([
            InlineKeyboardButton(text="🗑 Отменить запись", callback_data=f"event_cancel:{event_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="✅ Я пойду", callback_data=f"event_going:{event_id}"),
            InlineKeyboardButton(text="❓ Возможно", callback_data=f"event_maybe:{event_id}"),
        ])

    # Кнопка "Друзья на событии"
    buttons.append([
        InlineKeyboardButton(text="👥 Друзья на событии", callback_data=f"event_friends:{event_id}")
    ])

    # Кнопка "Пригласить друга"
    buttons.append([
        InlineKeyboardButton(text="📤 Пригласить друга", callback_data=f"event_invite:{event_id}")
    ])

    # Кнопка "К списку"
    buttons.append([
        InlineKeyboardButton(text="📋 К списку", callback_data="events_list")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_list_keyboard(
    events: list,
    page: int = 1,
    total_pages: int = 1,
    category: str | None = None,
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру со списком событий.

    Args:
        events: Список событий
        page: Текущая страница
        total_pages: Всего страниц
        category: Категория событий

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    # Кнопки событий (по 1 на строку)
    for event in events[:5]:  # Показываем максимум 5 событий
        date_str = event.date_start.strftime("%d.%m")
        button_text = f"{date_str} - {event.title[:30]}"
        if len(event.title) > 30:
            button_text += "..."

        buttons.append([
            InlineKeyboardButton(
                text=button_text, callback_data=f"event_view:{event.id}"
            )
        ])

    # Пагинация
    if total_pages > 1:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"events_page:{page - 1}:{category or 'all'}",
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
        )

        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡️ Вперед",
                    callback_data=f"events_page:{page + 1}:{category or 'all'}",
                )
            )

        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
