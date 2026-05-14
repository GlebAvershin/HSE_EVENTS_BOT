"""Модуль аутентификации администраторов."""
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.base import get_session
from src.database.models.admin_user import AdminUser


# --- Pydantic schemas ---


class TokenResponse(BaseModel):
    """Ответ с токенами."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# --- Auth Service ---


class AuthService:
    """Сервис аутентификации администраторов."""

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Хешировать пароль."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Создать access token (30 мин по умолчанию)."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta
            if expires_delta
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.API_ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Создать refresh token (7 дней)."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.API_ALGORITHM)


auth_service = AuthService()


async def get_current_admin(
    token: str = Depends(AuthService.oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> AdminUser:
    """Dependency для получения текущего администратора из JWT токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.API_SECRET_KEY, algorithms=[settings.API_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if username is None or token_type != "access":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    result = await session.execute(
        select(AdminUser).where(AdminUser.username == username)
    )
    admin = result.scalar_one_or_none()

    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin


# --- Router ---

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Аутентификация администратора. Возвращает access и refresh токены."""
    # Найти пользователя
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == form_data.username)
    )
    admin = result.scalar_one_or_none()

    # Проверить существование и активность
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверить пароль
    if not auth_service.verify_password(form_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Обновить last_login_at
    admin.last_login_at = datetime.utcnow()
    await session.commit()

    # Создать токены
    token_data = {"sub": admin.username}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
