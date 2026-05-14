"""Роутер для управления источниками событий в админ-панели."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.admin.auth import get_current_admin
from src.database.base import get_session
from src.database.models.admin_user import AdminUser
from src.database.models.event_source import EventSource


# --- Pydantic schemas ---


class SourceResponse(BaseModel):
    """Ответ с данными источника."""

    id: int
    name: str
    url: str | None = None
    parser_type: str
    is_active: bool
    last_parsed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceCreateRequest(BaseModel):
    """Запрос на создание источника."""

    name: str
    url: str | None = None
    parser_type: str
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("parser_type")
    @classmethod
    def validate_parser_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("parser_type must not be empty")
        return v.strip()


class SourceUpdateRequest(BaseModel):
    """Запрос на обновление источника (частичное обновление)."""

    name: str | None = None
    url: str | None = None
    parser_type: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v.strip() if v is not None else v

    @field_validator("parser_type")
    @classmethod
    def validate_parser_type(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("parser_type must not be empty")
        return v.strip() if v is not None else v


# --- Router ---

router = APIRouter(prefix="/api/admin/sources", tags=["admin-sources"])


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[SourceResponse]:
    """Получить список всех источников."""
    result = await session.execute(select(EventSource))
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> SourceResponse:
    """Создать новый источник."""
    source = EventSource(
        name=data.name,
        url=data.url,
        parser_type=data.parser_type,
        is_active=data.is_active,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> SourceResponse:
    """Частичное обновление источника."""
    result = await session.execute(
        select(EventSource).where(EventSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await session.commit()
    await session.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удалить источник."""
    result = await session.execute(
        select(EventSource).where(EventSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )

    await session.delete(source)
    await session.commit()
