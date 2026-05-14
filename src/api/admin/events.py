"""Роутер для управления событиями в админ-панели."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.admin.auth import get_current_admin
from src.database.base import get_session
from src.database.models.admin_user import AdminUser
from src.database.models.event import Event


# --- Pydantic schemas ---


class EventResponse(BaseModel):
    """Ответ с данными события."""

    id: int
    title: str
    description: str | None = None
    category: str
    date_start: datetime
    date_end: datetime | None = None
    location: str | None = None
    address: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    is_moderated: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Ответ со списком событий и пагинацией."""

    items: list[EventResponse]
    total: int
    page: int
    page_size: int


def _strip_tz(v: datetime | None) -> datetime | None:
    if v is None:
        return None
    if v.tzinfo is not None:
        v = v.astimezone(tz=None).replace(tzinfo=None)
    return v


class EventUpdateRequest(BaseModel):
    """Запрос на обновление события (частичное обновление)."""

    title: str | None = None
    description: str | None = None
    category: str | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None
    location: str | None = None
    address: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    is_published: bool | None = None
    is_moderated: bool | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is not None and v not in ("it", "entertainment"):
            raise ValueError("category must be 'it' or 'entertainment'")
        return v

    @field_validator("date_start", "date_end")
    @classmethod
    def strip_tz(cls, v: datetime | None) -> datetime | None:
        return _strip_tz(v)


class EventCreateRequest(BaseModel):
    """Запрос на создание события вручную."""

    title: str
    description: str | None = None
    category: str
    date_start: datetime
    date_end: datetime | None = None
    location: str | None = None
    address: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    is_published: bool = False

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in ("it", "entertainment"):
            raise ValueError("category must be 'it' or 'entertainment'")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("date_start", "date_end")
    @classmethod
    def strip_tz(cls, v: datetime | None) -> datetime | None:
        return _strip_tz(v)


# --- Router ---

router = APIRouter(prefix="/api/admin/events", tags=["admin-events"])


@router.get("/", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EventListResponse:
    """Получить список событий с фильтрацией и пагинацией."""
    query = select(Event)
    count_query = select(func.count(Event.id))

    # Фильтр по статусу
    if status == "pending":
        query = query.where(Event.is_moderated == False)
        count_query = count_query.where(Event.is_moderated == False)
    elif status == "published":
        query = query.where(Event.is_published == True)
        count_query = count_query.where(Event.is_published == True)

    # Фильтр по категории
    if category is not None:
        query = query.where(Event.category == category)
        count_query = count_query.where(Event.category == category)

    # Поиск по title/description (ILIKE)
    if search is not None:
        pattern = f"%{search}%"
        search_condition = or_(
            Event.title.ilike(pattern),
            Event.description.ilike(pattern),
        )
        query = query.where(search_condition)
        count_query = count_query.where(search_condition)

    # Получить общее количество
    total = await session.scalar(count_query) or 0

    # Пагинация и сортировка
    offset = (page - 1) * page_size
    query = query.order_by(Event.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    items = list(result.scalars().all())

    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """Создать событие вручную."""
    event = Event(
        title=data.title,
        description=data.description,
        category=data.category,
        date_start=data.date_start,
        date_end=data.date_end,
        location=data.location,
        address=data.address,
        source_url=data.source_url,
        image_url=data.image_url,
        is_published=data.is_published,
        is_moderated=data.is_published,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return EventResponse.model_validate(event)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """Получить событие по ID."""
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return EventResponse.model_validate(event)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """Частичное обновление события."""
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Обновить только переданные поля (non-None)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    # Обновить updated_at
    event.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(event)

    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удалить событие."""
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    await session.delete(event)
    await session.commit()


@router.post("/{event_id}/publish", response_model=EventResponse)
async def publish_event(
    event_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """Опубликовать событие (идемпотентная операция)."""
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    event.is_published = True
    event.is_moderated = True
    event.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(event)

    return EventResponse.model_validate(event)
