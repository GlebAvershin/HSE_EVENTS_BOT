"""Сервис для работы с друзьями."""
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.friendship import FriendshipRepository
from src.database.repositories.user import UserRepository
from src.database.models.user import User


class FriendshipService:
    """Сервис для работы с друзьями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.friendship_repo = FriendshipRepository(session)
        self.user_repo = UserRepository(session)

    async def get_friends_list(self, user_id: int) -> list[User]:
        """
        Получить список друзей.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список друзей
        """
        return await self.friendship_repo.get_friends(user_id)

    async def get_pending_requests(self, user_id: int) -> list[User]:
        """
        Получить входящие запросы в друзья.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список пользователей
        """
        return await self.friendship_repo.get_pending_requests(user_id)

    async def get_sent_requests(self, user_id: int) -> list[User]:
        """
        Получить исходящие запросы в друзья.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список пользователей
        """
        return await self.friendship_repo.get_sent_requests(user_id)

    async def send_friend_request(
        self, user_id: int, friend_username: str
    ) -> tuple[bool, str]:
        """
        Отправить запрос в друзья.

        Args:
            user_id: ID пользователя
            friend_username: Username друга

        Returns:
            tuple[bool, str]: (Успех, Сообщение)
        """
        # Ищем пользователя по username
        friend = await self.user_repo.get_by_username(friend_username)

        if not friend:
            return False, "❌ Пользователь не найден"

        if friend.id == user_id:
            return False, "❌ Нельзя добавить себя в друзья"

        # Проверяем существующую связь
        status = await self.friendship_repo.get_friendship_status(user_id, friend.id)

        if status == "accepted":
            return False, "❌ Вы уже друзья"

        if status == "pending":
            return False, "❌ Запрос уже отправлен"

        # Проверяем обратную связь (возможно нам уже отправили запрос)
        reverse_status = await self.friendship_repo.get_friendship_status(
            friend.id, user_id
        )

        if reverse_status == "pending":
            # Автоматически принимаем
            await self.friendship_repo.accept_friendship(user_id, friend.id)
            return True, f"✅ Вы стали друзьями с @{friend.username}"

        # Создаем новый запрос
        await self.friendship_repo.create_friendship_request(user_id, friend.id)
        return True, f"✅ Запрос отправлен пользователю @{friend.username}"

    async def accept_request(self, user_id: int, friend_id: int) -> tuple[bool, str]:
        """
        Принять запрос в друзья.

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            tuple[bool, str]: (Успех, Сообщение)
        """
        success = await self.friendship_repo.accept_friendship(user_id, friend_id)

        if success:
            friend = await self.user_repo.get_by_id(friend_id)
            return True, f"✅ Вы стали друзьями с @{friend.username}"

        return False, "❌ Не удалось принять запрос"

    async def reject_request(self, user_id: int, friend_id: int) -> tuple[bool, str]:
        """
        Отклонить запрос в друзья.

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            tuple[bool, str]: (Успех, Сообщение)
        """
        success = await self.friendship_repo.reject_friendship(user_id, friend_id)

        if success:
            return True, "✅ Запрос отклонен"

        return False, "❌ Не удалось отклонить запрос"

    async def remove_friend(self, user_id: int, friend_id: int) -> tuple[bool, str]:
        """
        Удалить из друзей.

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            tuple[bool, str]: (Успех, Сообщение)
        """
        success = await self.friendship_repo.remove_friendship(user_id, friend_id)

        if success:
            return True, "✅ Пользователь удален из друзей"

        return False, "❌ Не удалось удалить из друзей"

    def format_user_info(self, user: User, show_username: bool = True) -> str:
        """
        Форматировать информацию о пользователе.

        Args:
            user: Пользователь
            show_username: Показывать username

        Returns:
            str: Отформатированная информация
        """
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"

        if show_username and user.username:
            name += f" (@{user.username})"

        return name
