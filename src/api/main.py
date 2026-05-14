"""FastAPI приложение."""
import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from src.api.admin.auth import router as admin_auth_router
from src.api.admin.events import router as admin_events_router
from src.api.admin.sources import router as admin_sources_router
from src.api.admin.stats import router as admin_stats_router
from src.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NN Events API",
    description="API для агрегатора событий Нижнего Новгорода",
    version="0.1.0",
)

# CORS configuration: restrict origins in production via ADMIN_PANEL_ORIGIN env var
origins = (
    [settings.ADMIN_PANEL_ORIGIN]
    if settings.ADMIN_PANEL_ORIGIN != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handlers ---


@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors with HTTP 503."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service temporarily unavailable. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Handle unexpected errors with HTTP 500."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


# --- Simple in-memory rate limiter for login endpoint ---

# Stores {ip: [(timestamp, ...), ...]} for login attempts
_login_attempts: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_MAX_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 60


@app.middleware("http")
async def rate_limit_login(request: Request, call_next):
    """Rate limit login endpoint: 5 attempts per minute per IP."""
    if request.url.path == "/api/admin/auth/login" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean up old attempts outside the window
        _login_attempts[client_ip] = [
            t for t in _login_attempts[client_ip]
            if now - t < _RATE_LIMIT_WINDOW_SECONDS
        ]

        if len(_login_attempts[client_ip]) >= _RATE_LIMIT_MAX_ATTEMPTS:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many login attempts. Please try again later."},
            )

        # Record this attempt
        _login_attempts[client_ip].append(now)

    response = await call_next(request)
    return response


# Admin panel routes
app.include_router(admin_auth_router)
app.include_router(admin_events_router)
app.include_router(admin_stats_router)
app.include_router(admin_sources_router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"status": "ok", "service": "nn-events-api"}


@app.get("/health")
async def health():
    """Проверка состояния сервиса."""
    return {"status": "healthy"}
