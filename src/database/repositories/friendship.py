"""Репозиторий для работы с дружескими связями."""
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.friendship import Friendship
from src.database.models.user import User


class FriendshipRepository:
    """Репозиторий для работы с дружескими связями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    async def get_friendship(self, user_id: int, friend_id: int) -> Friendship | None:
        """
        Получить дружескую связь между двумя пользователями.

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            Friendship | None: Дружеская связь или None
        """
        result = await self.session.execute(
            select(Friendship).where(
                and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id)
            )
        )
        return result.scalar_one_or_none()

    async def create_friendship_request(
        self, user_id: int, friend_id: int
    ) -> Friendship:
        """
        Создать запрос на добавление в друзья.

        Args:
            user_id: ID пользователя, отправляющего запрос
            friend_id: ID пользователя, получающего запрос

        Returns:
            Friendship: Созданная дружеская связь
        """
        friendship = Friendship(
            user_id=user_id, friend_id=friend_id, status="pending"
        )

        self.session.add(friendship)
        await self.session.commit()
        await self.session.refresh(friendship)

        return friendship

    async def accept_friendship(self, user_id: int, friend_id: int) -> bool:
        """
        Принять запрос на добавление в друзья (двусторонняя связь).

        Args:
            user_id: ID пользователя, принимающего запрос
            friend_id: ID пользователя, отправившего запрос

        Returns:
            bool: True если успешно
        """
        # Находим запрос от friend_id к user_id
        friendship = await self.get_friendship(friend_id, user_id)

        if not friendship or friendship.status != "pending":
            return False

        # Обновляем статус на accepted
        friendship.status = "accepted"

        # Создаем обратную связь
        reverse_friendship = Friendship(
            user_id=user_id, friend_id=friend_id, status="accepted"
        )
        self.session.add(reverse_friendship)

        await self.session.commit()
        return True

    async def reject_friendship(self, user_id: int, friend_id: int) -> bool:
        """
        Отклонить запрос на добавление в друзья.

        Args:
            user_id: ID пользователя, отклоняющего запрос
            friend_id: ID пользователя, отправившего запрос

        Returns:
            bool: True если успешно
        """
        friendship = await self.get_friendship(friend_id, user_id)

        if not friendship or friendship.status != "pending":
            return False

        friendship.status = "rejected"
        await self.session.commit()
        return True

    async def remove_friendship(self, user_id: int, friend_id: int) -> bool:
        """
        Удалить из друзей (двусторонняя операция).

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            bool: True если успешно
        """
        # Удаляем обе связи
        result1 = await self.session.execute(
            select(Friendship).where(
                and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id)
            )
        )
        friendship1 = result1.scalar_one_or_none()

        result2 = await self.session.execute(
            select(Friendship).where(
                and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id)
            )
        )
        friendship2 = result2.scalar_one_or_none()

        if friendship1:
            await self.session.delete(friendship1)
        if friendship2:
            await self.session.delete(friendship2)

        await self.session.commit()
        return True

    async def get_friends(self, user_id: int) -> list[User]:
        """
        Получить список друзей пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список друзей
        """
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(User)
            .join(Friendship, Friendship.friend_id == User.id)
            .where(
                and_(
                    Friendship.user_id == user_id, Friendship.status == "accepted"
                )
            )
            .order_by(User.first_name)
        )

        return list(result.scalars().all())

    async def get_pending_requests(self, user_id: int) -> list[User]:
        """
        Получить список входящих запросов в друзья.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список пользователей, отправивших запросы
        """
        result = await self.session.execute(
            select(User)
            .join(Friendship, Friendship.user_id == User.id)
            .where(
                and_(
                    Friendship.friend_id == user_id, Friendship.status == "pending"
                )
            )
            .order_by(Friendship.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_sent_requests(self, user_id: int) -> list[User]:
        """
        Получить список исходящих запросов в друзья.

        Args:
            user_id: ID пользователя

        Returns:
            list[User]: Список пользователей, которым отправлены запросы
        """
        result = await self.session.execute(
            select(User)
            .join(Friendship, Friendship.friend_id == User.id)
            .where(
                and_(Friendship.user_id == user_id, Friendship.status == "pending")
            )
            .order_by(Friendship.created_at.desc())
        )

        return list(result.scalars().all())

    async def are_friends(self, user_id: int, friend_id: int) -> bool:
        """
        Проверить являются ли пользователи друзьями.

        Args:
            user_id: ID первого пользователя
            friend_id: ID второго пользователя

        Returns:
            bool: True если друзья
        """
        friendship = await self.get_friendship(user_id, friend_id)
        return friendship is not None and friendship.status == "accepted"

    async def get_friendship_status(
        self, user_id: int, friend_id: int
    ) -> str | None:
        """
        Получить статус дружбы между пользователями.

        Args:
            user_id: ID пользователя
            friend_id: ID друга

        Returns:
            str | None: Статус ('accepted', 'pending', 'rejected') или None
        """
        friendship = await self.get_friendship(user_id, friend_id)
        return friendship.status if friendship else None
