"""Парсер Яндекс.Афиши для Нижнего Новгорода.

СТАТУС: ОТКЛЮЧЁН
Яндекс.Афиша блокирует headless-браузеры (показывает SmartCaptcha).
Для работы нужен либо:
- Резидентный прокси + fingerprint spoofing
- Официальный API (не существует публично)
- Ручной парсинг через cookies авторизованной сессии

Парсер возвращает пустой список.
"""
from typing import List

from src.parsers.base import BaseParser, EventData


class YandexAfishaParser(BaseParser):
    """
    Парсер событий с Яндекс.Афиши.
    
    СТАТУС: ОТКЛЮЧЁН (SmartCaptcha блокирует автоматические запросы)
    """
    
    def __init__(self):
        super().__init__(
            source_name="Yandex.Afisha [DISABLED: captcha]",
            source_url="https://afisha.yandex.ru/nizhny-novgorod"
        )
    
    async def parse(self) -> List[EventData]:
        """Яндекс блокирует headless-браузеры. Возвращает пустой список."""
        print(f"  [SKIP] {self.source_name}: blocked by SmartCaptcha")
        return []
