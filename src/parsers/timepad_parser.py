"""Парсер Timepad — IT-мероприятия в Нижнем Новгороде."""
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from src.parsers.browser_parser import BrowserParser
from src.parsers.base import EventData
from src.parsers.date_utils import _guess_year


class TimepadParser(BrowserParser):
    """
    Парсер событий с afisha.timepad.ru.
    
    Сайт — SPA, требуется headless-браузер.
    """
    
    PAGE_LOAD_TIMEOUT = 60000
    NETWORK_IDLE_TIMEOUT = 25000
    
    def __init__(self):
        super().__init__(
            source_name="Timepad",
            source_url="https://afisha.timepad.ru/nizhniy-novgorod/categories/it-i-internet"
        )
    
    async def _parse_with_browser(self) -> List[EventData]:
        """Парсить события через Playwright."""
        try:
            html = await self.fetch_rendered_html(
                self.source_url,
                wait_selector="a[href*='/events/']"
            )
        except Exception:
            # Fallback: загружаем без wait_selector
            html = await self.fetch_rendered_html(self.source_url)
        return self._extract_events(html)
    
    def _extract_events(self, html: str) -> List[EventData]:
        """Извлечь события из отрендеренного HTML."""
        events = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Ссылки на события Timepad: /nizhniy-novgorod/events/SLUG или /events/SLUG
        event_links = soup.find_all("a", href=re.compile(
            r"(/events/[a-z0-9\-]+|/event/\d+|timepad\.ru/event/\d+)"
        ))
        
        seen_urls = set()
        
        for link in event_links[:30]:
            try:
                event = self._parse_link(link)
                if event and event.source_url not in seen_urls:
                    seen_urls.add(event.source_url)
                    events.append(event)
            except Exception:
                continue
        
        return events
    
    def _parse_link(self, link) -> Optional[EventData]:
        """Парсить ссылку на событие."""
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https:{href}" if href.startswith("//") else f"https://afisha.timepad.ru{href}"
        href = href.split("?")[0].split("#")[0]
        
        # Пропускаем "categories" и навигационные ссылки
        if "/categories/" in href or "/organizations/" in href:
            return None
        
        # Заголовок — текст ссылки или h-элемент внутри
        title_elem = link.find(["h1", "h2", "h3", "h4"])
        if title_elem:
            title = self.clean_text(title_elem.get_text())
        else:
            title = self.clean_text(link.get_text())
        
        if not title or len(title) < 5:
            return None
        
        # Пропускаем навигационные
        if title.lower() in ("регистрация", "купить билет", "подробнее"):
            return None
        
        # Дата из родителя
        parent = link.find_parent(["div", "article", "li"])
        date_start = None
        if parent:
            text = parent.get_text(separator=" ", strip=True)
            date_start = self._extract_date(text)
        
        if not date_start:
            now = datetime.now()
            year = now.year + (1 if now.month >= 12 else 0)
            month = 1 if now.month >= 12 else now.month + 1
            date_start = datetime(year, month, 15, 19, 0)
        
        # Изображение
        image_url = None
        if parent:
            img = parent.find("img")
            if img:
                image_url = img.get("src") or img.get("data-src")
                if image_url and image_url.startswith("//"):
                    image_url = f"https:{image_url}"
        
        return EventData(
            title=title[:500],
            description=title,
            category="it",
            date_start=date_start,
            location="Нижний Новгород",
            source_url=href,
            image_url=image_url,
        )
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Извлечь дату из текста."""
        match = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)',
            text, re.IGNORECASE
        )
        if not match:
            return None
        
        day = int(match.group(1))
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
        }
        month = months.get(match.group(2).lower())
        if not month:
            return None
        
        year = _guess_year(month)
        
        time_match = re.search(r'(\d{1,2}):(\d{2})', text[match.end():match.end() + 30])
        hour, minute = 19, 0
        if time_match:
            h, m = int(time_match.group(1)), int(time_match.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                hour, minute = h, m
        
        try:
            dt = datetime(year, month, day, hour, minute)
            if dt < datetime.now():
                return None
            return dt
        except ValueError:
            return None
