"""Конфигурация приложения."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram Bot
    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "nn_events"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # VK API
    VK_API_TOKEN: str = ""

    # FastAPI
    API_SECRET_KEY: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Parsing
    PARSE_INTERVAL_HOURS: int = 6

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        """Получить URL базы данных."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Получить URL Redis."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def admin_ids_list(self) -> list[int]:
        """Получить список ID администраторов."""
        if not self.ADMIN_IDS:
            return []
        return [int(admin_id.strip()) for admin_id in self.ADMIN_IDS.split(",")]


settings = Settings()
