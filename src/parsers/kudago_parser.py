"""Парсер KudaGo API — события в Нижнем Новгороде.

KudaGo предоставляет бесплатный публичный REST API без авторизации.
Документация: https://docs.kudago.com/

Эндпоинт: GET /public-api/v1.4/events/
Параметры:
  - location=nnv (Нижний Новгород)
  - actual_since=UNIX_TIMESTAMP (только актуальные)
  - fields=... (выбор полей)
  - page_size=N
  - categories=... (фильтр по категориям)
"""
import time
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData


# Маппинг категорий KudaGo -> наши категории
KUDAGO_IT_CATEGORIES = {
    "business-events",
    "education",  # часто содержит IT-курсы и лекции
    "science",    # научно-технические события
}

KUDAGO_ENTERTAINMENT_CATEGORIES = {
    "concert", "theater", "party", "exhibition", "festival",
    "cinema", "show", "stand-up", "quest", "sport",
    "kids", "holiday", "other", "entertainment",
}

# Ключевые слова в названии/описании для определения IT
KUDAGO_IT_KEYWORDS = [
    "it", "айти", "программирование", "разработка",
    "хакатон", "митап", "meetup", "конференция",
    "tech", "технологии", "digital", "диджитал",
    "python", "javascript", "веб", "web",
    "data science", "машинное обучение", "ai",
    "devops", "backend", "frontend", "fullstack",
    "kubernetes", "docker", "api", "блокчейн",
]


class KudaGoParser(BaseParser):
    """
    Парсер событий через KudaGo API.
    
    Бесплатный публичный API, не требует авторизации.
    Возвращает события в Нижнем Новгороде с датами, местами и категориями.
    """
    
    API_BASE = "https://kudago.com/public-api/v1.4"
    LOCATION = "nnv"  # Нижний Новгород
    
    def __init__(self):
        super().__init__(
            source_name="KudaGo",
            source_url="https://kudago.com/nnv/events/"
        )
        self._places_cache: dict[int, dict] = {}
    
    async def _fetch_place(self, place_id: int) -> dict:
        """
        Получить информацию о месте по ID (с кэшированием).
        
        Returns:
            {"title": "...", "address": "..."} или пустой dict
        """
        if place_id in self._places_cache:
            return self._places_cache[place_id]
        
        try:
            url = f"{self.API_BASE}/places/{place_id}/?fields=id,title,address"
            data = await self.fetch_json(url)
            result = {
                "title": data.get("title", ""),
                "address": data.get("address", ""),
            }
            self._places_cache[place_id] = result
            return result
        except Exception:
            self._places_cache[place_id] = {}
            return {}
    
    async def parse(self) -> List[EventData]:
        """Парсить события через KudaGo API."""
        events = []
        
        try:
            # Получаем актуальные события
            now_ts = int(time.time())
            
            params = (
                f"?location={self.LOCATION}"
                f"&actual_since={now_ts}"
                f"&fields=id,title,description,dates,place,categories,site_url,images"
                f"&page_size=100"
                f"&order_by=date"
            )
            
            url = f"{self.API_BASE}/events/{params}"
            data = await self.fetch_json(url)
            
            results = data.get("results", [])
            
            for item in results:
                try:
                    event = await self._parse_event(item)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"  Error parsing KudaGo event: {e}")
                    continue
            
        except Exception as e:
            print(f"Error fetching KudaGo API: {e}")
        
        return events
    
    async def _parse_event(self, item: dict) -> Optional[EventData]:
        """Парсить одно событие из JSON."""
        title = item.get("title", "").strip()
        if not title:
            return None
        
        # Дата — берём первую актуальную
        dates = item.get("dates", [])
        date_start = self._get_nearest_date(dates)
        if not date_start:
            return None
        
        # Категория
        categories = item.get("categories", [])
        category = self._determine_category(
            categories,
            title=title,
            description=item.get("description", ""),
        )
        
        # URL
        site_url = item.get("site_url", "")
        if not site_url:
            event_id = item.get("id", "")
            site_url = f"https://kudago.com/nnv/event/{event_id}/"
        
        # Описание
        description = item.get("description", "")
        if description:
            from bs4 import BeautifulSoup
            description = BeautifulSoup(description, "html.parser").get_text()
            description = self.clean_text(description)[:500]
        if not description:
            description = title
        
        # Место — подтягиваем из API
        location = "Нижний Новгород"
        address = None
        place = item.get("place")
        if place and isinstance(place, dict):
            place_id = place.get("id")
            if place_id:
                place_info = await self._fetch_place(place_id)
                if place_info.get("title"):
                    location = place_info["title"]
                if place_info.get("address"):
                    address = place_info["address"]
        
        # Изображение
        image_url = None
        images = item.get("images", [])
        if images and isinstance(images, list) and len(images) > 0:
            image_url = images[0].get("image")
        
        return EventData(
            title=title[:500],
            description=description,
            category=category,
            date_start=date_start,
            location=location,
            address=address,
            source_url=site_url,
            image_url=image_url,
        )
    
    def _get_nearest_date(self, dates: list) -> Optional[datetime]:
        """Получить ближайшую актуальную дату."""
        now_ts = int(time.time())
        
        for date_info in dates:
            start_ts = date_info.get("start")
            if start_ts and start_ts >= now_ts:
                try:
                    dt = datetime.fromtimestamp(start_ts)
                    # Фильтруем невалидные даты (timestamp 0, слишком старые)
                    if dt.year >= 2024:
                        return dt
                except (ValueError, OSError):
                    continue
        
        # Если нет будущих дат — берём последнюю, но только если она валидная
        if dates:
            start_ts = dates[-1].get("start")
            if start_ts and start_ts > 1700000000:  # после 2023-11
                try:
                    dt = datetime.fromtimestamp(start_ts)
                    if dt.year >= 2024:
                        return dt
                except (ValueError, OSError):
                    pass
        
        return None
    
    def _determine_category(self, categories: list, title: str = "", description: str = "") -> str:
        """Определить категорию события."""
        # 1. Проверяем категории KudaGo
        for cat in categories:
            if cat in KUDAGO_IT_CATEGORIES:
                # Education/science — проверяем что это про IT
                if cat in ("education", "science"):
                    text = f"{title} {description}".lower()
                    if any(kw in text for kw in KUDAGO_IT_KEYWORDS):
                        return "it"
                else:
                    return "it"
        
        # 2. Проверяем ключевые слова в названии
        text = f"{title} {description}".lower()
        if any(kw in text for kw in KUDAGO_IT_KEYWORDS):
            return "it"
        
        return "entertainment"
