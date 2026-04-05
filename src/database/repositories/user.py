"""Репозиторий для работы с пользователями."""
import secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User
from src.database.models.user_settings import UserSettings


def generate_referral_code() -> str:
    """
    Генерировать уникальный реферальный код.

    Returns:
        str: Реферальный код (8 символов)
    """
    return secrets.token_urlsafe(6)[:8]


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User | None: Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    async def get_by_username(self, username: str) -> User | None:
        """
        Получить пользователя по username.

        Args:
            username: Username пользователя

        Returns:
            User | None: Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


    async def get_by_id(self, user_id: int) -> User | None:
        """
        Получить пользователя по ID.

        Args:
            user_id: ID пользователя

        Returns:
            User | None: Пользователь или None
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """
        Получить пользователя по username.

        Args:
            username: Username пользователя

        Returns:
            User | None: Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, referral_code: str) -> User | None:
        """
        Получить пользователя по реферальному коду.

        Args:
            referral_code: Реферальный код

        Returns:
            User | None: Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(User.referral_code == referral_code)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_admin: bool = False,
        referred_by: int | None = None,
    ) -> User:
        """
        Создать нового пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            is_admin: Является ли администратором
            referred_by: Telegram ID пригласившего пользователя

        Returns:
            User: Созданный пользователь
        """
        # Генерируем уникальный реферальный код
        referral_code = generate_referral_code()
        
        # Проверяем уникальность
        while await self.get_by_referral_code(referral_code):
            referral_code = generate_referral_code()
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            referral_code=referral_code,
            referred_by=referred_by,
        )
        self.session.add(user)
        await self.session.flush()

        # Создаем настройки по умолчанию
        settings = UserSettings(
            user_id=user.id,
            notify_new_events=True,
            notify_friend_going=True,
            notify_event_reminder=True,
            preferred_categories=["it", "entertainment"],
        )
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update(
        self,
        user: User,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """
        Обновить данные пользователя.

        Args:
            user: Пользователь
            username: Новый username
            first_name: Новое имя
            last_name: Новая фамилия

        Returns:
            User: Обновленный пользователь
        """
        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_admin: bool = False,
    ) -> tuple[User, bool]:
        """
        Получить или создать пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            is_admin: Является ли администратором

        Returns:
            tuple[User, bool]: Пользователь и флаг создания (True если создан)
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем данные если изменились
            if (
                user.username != username
                or user.first_name != first_name
                or user.last_name != last_name
            ):
                user = await self.update(user, username, first_name, last_name)
            return user, False

        user = await self.create(telegram_id, username, first_name, last_name, is_admin)
        return user, True
