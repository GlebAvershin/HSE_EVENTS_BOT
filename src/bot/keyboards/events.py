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
                KeyboardButton(text="🔍 Поиск"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите категорию...",
    )
    return keyboard


def get_events_filter_keyboard(category: str | None = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру фильтров событий.

    Args:
        category: Категория событий

    Returns:
        InlineKeyboardMarkup: Inline клавиатура с фильтрами
    """
    cat = category or "all"
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 На этой неделе",
                callback_data=f"events_filter:week:{cat}",
            ),
            InlineKeyboardButton(
                text="📅 В этом месяце",
                callback_data=f"events_filter:month:{cat}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔥 Популярные",
                callback_data=f"events_filter:popular:{cat}",
            ),
            InlineKeyboardButton(
                text="📋 Все",
                callback_data=f"events_filter:all:{cat}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🌐 Онлайн",
                callback_data=f"events_filter:online:{cat}",
            ),
            InlineKeyboardButton(
                text="📍 Офлайн",
                callback_data=f"events_filter:offline:{cat}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_detail_keyboard(
    event_id: int,
    user_status: str | None = None,
    show_rate: bool = False,
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для детального просмотра события.

    Args:
        event_id: ID события
        user_status: Статус пользователя ('going', 'maybe', None)
        show_rate: Показывать кнопку "Оценить" (для прошедших событий, где user attended)

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

    # Кнопка "Оценить" — только для прошедших событий, где пользователь был
    if show_rate:
        buttons.append([
            InlineKeyboardButton(text="⭐ Оценить", callback_data=f"event_rate:{event_id}")
        ])

    # Кнопка "Обсудить" — всегда видна
    buttons.append([
        InlineKeyboardButton(text="💬 Обсудить", callback_data=f"event_discuss:{event_id}")
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


def get_rating_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для выбора рейтинга (1-5 звёзд).

    Args:
        event_id: ID события

    Returns:
        InlineKeyboardMarkup: Inline клавиатура с кнопками рейтинга
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'⭐' * i}", callback_data=f"event_rate_submit:{event_id}:{i}"
            )
            for i in range(1, 6)
        ],
        [
            InlineKeyboardButton(text="🔙 Отмена", callback_data=f"event_view:{event_id}")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skip_comment_keyboard() -> InlineKeyboardMarkup:
    """
    Получить клавиатуру с кнопкой "Пропустить" для комментария к отзыву.

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = [
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="review_skip_comment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_comments_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для обсуждения события.

    Args:
        event_id: ID события

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = [
        [InlineKeyboardButton(text="✍️ Написать", callback_data=f"event_comment:{event_id}")],
        [InlineKeyboardButton(text="🔙 К событию", callback_data=f"event_view:{event_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
