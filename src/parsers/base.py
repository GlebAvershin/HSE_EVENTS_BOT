"""Базовый класс для парсеров событий."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup


class EventData:
    """Структура данных события."""
    
    def __init__(
        self,
        title: str,
        description: str,
        category: str,
        date_start: datetime,
        location: str,
        source_url: str,
        date_end: Optional[datetime] = None,
        address: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.category = category
        self.date_start = date_start
        self.date_end = date_end
        self.location = location
        self.address = address
        self.source_url = source_url
        self.image_url = image_url
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения в БД."""
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "location": self.location,
            "address": self.address,
            "source_url": self.source_url,
            "image_url": self.image_url,
            "is_published": True,
        }


class BaseParser(ABC):
    """Базовый класс для всех парсеров."""
    
    # Настройки HTTP
    REQUEST_TIMEOUT = 15  # секунд
    MAX_RETRIES = 2
    RETRY_DELAY = 2  # секунд между ретраями
    
    def __init__(self, source_name: str, source_url: str):
        """
        Инициализация парсера.
        
        Args:
            source_name: Название источника
            source_url: URL источника
        """
        self.source_name = source_name
        self.source_url = source_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Создать HTTP сессию."""
        timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрыть HTTP сессию."""
        if self.session:
            await self.session.close()
    
    async def fetch_html(self, url: str) -> str:
        """
        Получить HTML страницы с ретраями.
        
        Args:
            url: URL страницы
            
        Returns:
            HTML контент
            
        Raises:
            aiohttp.ClientError: При ошибке запроса после всех ретраев
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with self.session.get(url) as response:
                    if response.status == 403:
                        raise aiohttp.ClientResponseError(
                            response.request_info,
                            response.history,
                            status=403,
                            message="Access denied (bot blocked)"
                        )
                    if response.status == 429:
                        # Rate limited — ждём дольше
                        await asyncio.sleep(self.RETRY_DELAY * 3)
                        continue
                    response.raise_for_status()
                    return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
        
        raise last_error
    
    async def fetch_json(self, url: str) -> Dict:
        """
        Получить JSON данные с ретраями.
        
        Args:
            url: URL API
            
        Returns:
            JSON данные
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
        
        raise last_error
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Парсить HTML с помощью BeautifulSoup.
        
        Args:
            html: HTML контент
            
        Returns:
            BeautifulSoup объект
        """
        return BeautifulSoup(html, "html.parser")
    
    @abstractmethod
    async def parse(self) -> List[EventData]:
        """
        Парсить события из источника.
        
        Returns:
            Список событий
        """
        pass
    
    def normalize_category(self, raw_category: str) -> str:
        """
        Нормализовать категорию события.
        
        Args:
            raw_category: Сырая категория
            
        Returns:
            'it' или 'entertainment'
        """
        raw_category = raw_category.lower()
        
        # IT ключевые слова
        it_keywords = [
            "it", "айти", "программирование", "разработка", "developer",
            "хакатон", "митап", "meetup", "конференция", "tech", "технологии",
            "digital", "диджитал", "код", "code", "python", "javascript",
            "веб", "web", "мобильная разработка", "data", "данные",
            "искусственный интеллект", "ai", "machine learning", "devops",
            "backend", "frontend", "fullstack", "qa", "тестирование",
            "kubernetes", "docker", "cloud", "облако", "api",
        ]
        
        for keyword in it_keywords:
            if keyword in raw_category:
                return "it"
        
        return "entertainment"
    
    def clean_text(self, text: str) -> str:
        """
        Очистить текст от лишних символов.
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # Убрать лишние пробелы и переносы
        text = " ".join(text.split())
        
        return text.strip()
