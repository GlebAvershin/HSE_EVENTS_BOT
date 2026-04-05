"""Настройка логирования."""
import logging
import sys

from src.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Настроить логгер.

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
