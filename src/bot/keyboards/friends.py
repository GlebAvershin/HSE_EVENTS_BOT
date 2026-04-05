"""Клавиатуры для работы с друзьями."""
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_friends_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить главное меню друзей.

    Returns:
        ReplyKeyboardMarkup: Клавиатура меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Мои друзья"),
                KeyboardButton(text="📨 Запросы"),
            ],
            [
                KeyboardButton(text="➕ Добавить друга"),
                KeyboardButton(text="🔗 Пригласить друга"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )
    return keyboard


def get_friends_list_keyboard(friends: list) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру со списком друзей.

    Args:
        friends: Список друзей

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    for friend in friends:
        name = friend.first_name
        if friend.last_name:
            name += f" {friend.last_name}"

        button_text = f"👤 {name}"
        if friend.username:
            button_text += f" (@{friend.username})"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text, callback_data=f"friend_view:{friend.id}"
                )
            ]
        )

    if not buttons:
        buttons.append(
            [InlineKeyboardButton(text="➕ Добавить друга", callback_data="friend_add")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_friend_detail_keyboard(friend_id: int) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для просмотра друга.

    Args:
        friend_id: ID друга

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Удалить из друзей", callback_data=f"friend_remove:{friend_id}"
            )
        ],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="friends_list")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pending_requests_keyboard(requests: list) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру с входящими запросами.

    Args:
        requests: Список запросов

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    for user in requests:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"

        button_text = f"👤 {name}"
        if user.username:
            button_text += f" (@{user.username})"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=button_text, callback_data=f"request_view:{user.id}"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_request_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру действий с запросом.

    Args:
        user_id: ID пользователя

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Принять", callback_data=f"request_accept:{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить", callback_data=f"request_reject:{user_id}"
            ),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="requests_list")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sent_requests_keyboard(requests: list) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру с исходящими запросами.

    Args:
        requests: Список запросов

    Returns:
        InlineKeyboardMarkup: Inline клавиатура
    """
    buttons = []

    for user in requests:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"

        button_text = f"⏳ {name}"
        if user.username:
            button_text += f" (@{user.username})"

        buttons.append([InlineKeyboardButton(text=button_text, callback_data="noop")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
