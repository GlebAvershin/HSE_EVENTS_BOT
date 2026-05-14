"""Скрипт для создания администратора панели управления.

Использование:
    python scripts/create_admin.py <username> <password>
    python scripts/create_admin.py  (интерактивный режим)
    python -m scripts.create_admin <username> <password>
"""
import asyncio
import sys
from getpass import getpass

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database.models.admin_user import AdminUser


def hash_password(password: str) -> str:
    """Хешировать пароль с bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def create_admin_user(username: str, password: str) -> None:
    """Создать администратора в базе данных."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Проверить, существует ли пользователь
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(f"Error: Admin user '{username}' already exists.")
            await engine.dispose()
            sys.exit(1)

        # Создать нового администратора
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    await engine.dispose()
    print(f"Admin user '{username}' created successfully.")


def main() -> None:
    """Точка входа скрипта."""
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 2:
        username = sys.argv[1]
        password = getpass("Password: ")
    else:
        username = input("Username: ")
        password = getpass("Password: ")

    if not username.strip():
        print("Error: Username cannot be empty.")
        sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters.")
        sys.exit(1)

    asyncio.run(create_admin_user(username.strip(), password))


if __name__ == "__main__":
    main()
