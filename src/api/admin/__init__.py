"""Admin panel API module.

Aggregates all admin routers for convenient inclusion in the FastAPI app.
"""
from src.api.admin.auth import router as auth_router
from src.api.admin.events import router as events_router
from src.api.admin.sources import router as sources_router
from src.api.admin.stats import router as stats_router

__all__ = ["auth_router", "events_router", "sources_router", "stats_router"]
