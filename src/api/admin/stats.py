"""Роутер для статистики в админ-панели."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.admin.auth import get_current_admin
from src.database.base import get_session
from src.database.models.admin_user import AdminUser
from src.database.models.event import Event
from src.database.models.event_source import EventSource
from src.database.models.user import User


# --- Pydantic schemas ---


class SourceStatusResponse(BaseModel):
    """Статус источника событий."""

    id: int
    name: str
    parser_type: str
    is_active: bool
    last_parsed_at: datetime | None = None

    class Config:
        from_attributes = True


class RecentEventResponse(BaseModel):
    """Краткая инфа о событии для ленты."""

    id: int
    title: str
    category: str
    date_start: datetime
    is_published: bool

    class Config:
        from_attributes = True


class CategoryCount(BaseModel):
    category: str
    count: int


class StatsResponse(BaseModel):
    """Ответ со статистикой."""

    events_total: int
    events_published: int
    events_pending: int
    users_total: int
    sources: list[SourceStatusResponse]
    events_by_category: list[CategoryCount] = []
    recent_events: list[RecentEventResponse] = []


# --- Router ---

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])


@router.get("/", response_model=StatsResponse)
async def get_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    """Получить статистику для дашборда."""
    # Подсчёт событий
    events_total = await session.scalar(select(func.count(Event.id))) or 0
    events_published = await session.scalar(
        select(func.count(Event.id)).where(Event.is_published == True)
    ) or 0
    events_pending = await session.scalar(
        select(func.count(Event.id)).where(Event.is_published == False)
    ) or 0

    # Подсчёт пользователей
    users_total = await session.scalar(select(func.count(User.id))) or 0

    # Список источников
    result = await session.execute(select(EventSource))
    sources = [
        SourceStatusResponse.model_validate(s) for s in result.scalars().all()
    ]

    # Распределение событий по категориям
    cat_result = await session.execute(
        select(Event.category, func.count(Event.id)).group_by(Event.category)
    )
    events_by_category = [
        CategoryCount(category=row[0], count=row[1]) for row in cat_result.all()
    ]

    # Последние события
    recent_result = await session.execute(
        select(Event).order_by(Event.created_at.desc()).limit(6)
    )
    recent_events = [
        RecentEventResponse.model_validate(e) for e in recent_result.scalars().all()
    ]

    return StatsResponse(
        events_total=events_total,
        events_published=events_published,
        events_pending=events_pending,
        users_total=users_total,
        sources=sources,
        events_by_category=events_by_category,
        recent_events=recent_events,
    )
