"""Парсер Milo Concert Hall."""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import parse_russian_date, MONTHS_RU, _guess_year


class MiloParser(BaseParser):
    """
    Парсер событий с Milo Concert Hall.
    
    Сайт отдаёт HTML в кодировке windows-1251.
    Структура: карточки с названием (ссылка на /afisha/slug/),
    датой ("08 мая"), временем ("23:00").
    """
    
    def __init__(self):
        super().__init__(
            source_name="Milo Concert Hall",
            source_url="https://miloconcerthall.ru/afisha/"
        )
    
    async def fetch_html(self, url: str) -> str:
        """Переопределяем для обработки windows-1251."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        import asyncio
        import aiohttp
        
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    # Читаем байты и декодируем вручную
                    raw_bytes = await response.read()
                    # Пробуем windows-1251, потом utf-8
                    try:
                        return raw_bytes.decode("windows-1251")
                    except UnicodeDecodeError:
                        return raw_bytes.decode("utf-8", errors="replace")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
        
        raise last_error
    
    async def parse(self) -> List[EventData]:
        """Парсить события с Milo Concert Hall."""
        events = []
        
        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)
            
            # Ищем все ссылки на /afisha/slug/
            links = soup.find_all("a", href=re.compile(r"/afisha/[a-z0-9\-]+/?$"))
            
            # Собираем уникальные события
            seen_urls = set()
            for link in links:
                href = link.get("href", "")
                title = self.clean_text(link.get_text())
                
                # Пропускаем навигационные и пустые ссылки
                if not title or len(title) < 2:
                    continue
                if title.lower() in {"milo concert hall", "подробнее", "купить билет"}:
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                try:
                    event = self._parse_event_from_context(link, href, title)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"  Error parsing Milo event '{title}': {e}")
                    continue
        
        except Exception as e:
            print(f"Error fetching Milo: {e}")
        
        return events
    
    def _parse_event_from_context(self, link, href: str, title: str) -> Optional[EventData]:
        """Парсить событие из ссылки и окружающего контекста."""
        # URL
        if not href.startswith("http"):
            event_url = f"https://miloconcerthall.ru{href}"
        else:
            event_url = href
        
        # Ищем дату и время в окружающем тексте (поднимаемся по DOM)
        date_start = None
        
        # Проходим по родительским элементам
        for parent in link.parents:
            if parent.name in ("body", "html", "[document]"):
                break
            
            parent_text = parent.get_text(separator=" ")
            
            # Ищем паттерн "DD месяц"
            date_match = re.search(
                r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|'
                r'августа|сентября|октября|ноября|декабря)',
                parent_text, re.IGNORECASE
            )
            
            if date_match:
                day = int(date_match.group(1))
                month_name = date_match.group(2).lower()
                month = MONTHS_RU.get(month_name)
                
                if month and 1 <= day <= 31:
                    year = _guess_year(month)
                    
                    # Ищем время
                    time_match = re.search(r'(\d{1,2}):(\d{2})', parent_text)
                    hour, minute = 19, 0
                    if time_match:
                        h = int(time_match.group(1))
                        m = int(time_match.group(2))
                        if 0 <= h <= 23 and 0 <= m <= 59:
                            hour, minute = h, m
                    
                    try:
                        date_start = datetime(year, month, day, hour, minute)
                    except ValueError:
                        pass
                
                break  # Нашли родителя с датой — выходим
        
        if not date_start:
            return None
        
        return EventData(
            title=title,
            description=title,
            category="entertainment",
            date_start=date_start,
            location="Milo Concert Hall, ул. Родионова 4, Нижний Новгород",
            source_url=event_url,
        )
