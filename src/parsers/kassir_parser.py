"""Парсер Kassir.ru для Нижнего Новгорода через headless-браузер."""
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from src.parsers.browser_parser import BrowserParser
from src.parsers.base import EventData
from src.parsers.date_utils import parse_russian_date, MONTHS_RU, _guess_year


class KassirParser(BrowserParser):
    """
    Парсер событий с Kassir.ru через Playwright.
    
    Kassir.ru — SPA, контент рендерится JavaScript'ом.
    Структура: карточки с названием, датой, временем, местом и ценой.
    Формат даты: "15 августа 20:00" или "27 июня 19:30"
    """
    
    def __init__(self):
        super().__init__(
            source_name="Kassir.ru",
            source_url="https://nn.kassir.ru/bilety-na-koncert"
        )
    
    async def _parse_with_browser(self) -> List[EventData]:
        """Парсить события с Kassir.ru."""
        html = await self.fetch_rendered_html(
            self.source_url,
            wait_selector="a[href*='/koncert/']"
        )
        return self._extract_events(html)
    
    def _extract_events(self, html: str) -> List[EventData]:
        """Извлечь события из отрендеренного HTML."""
        events = []
        soup = BeautifulSoup(html, "html.parser")
        
        # На Kassir.ru события — ссылки на /koncert/, /shou/, /festivali/ и т.д.
        event_links = soup.find_all("a", href=re.compile(
            r"^/(koncert|shou|festivali|teatr)/[a-z0-9\-]"
        ))
        
        seen_urls = set()
        for link in event_links:
            href = link.get("href", "")
            
            # Нормализуем URL
            if not href.startswith("http"):
                if href.startswith("/"):
                    href = f"https://nn.kassir.ru{href}"
                else:
                    href = f"https://nn.kassir.ru/{href}"
            
            # Убираем якоря
            href = href.split("#")[0]
            
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            try:
                event = self._parse_event_link(link, href)
                if event:
                    events.append(event)
            except Exception:
                continue
        
        return events[:30]
    
    def _parse_event_link(self, link, event_url: str) -> Optional[EventData]:
        """Парсить одну ссылку на событие."""
        # Получаем текст ссылки и окружающий контекст
        link_text = link.get_text(separator=" ")
        link_text = self.clean_text(link_text)
        
        if not link_text or len(link_text) < 3:
            return None
        
        # Пропускаем навигационные ссылки
        skip_patterns = [
            "показать ещё", "подробнее", "купить билет",
            "kassir.ru", "афиша", "загрузить",
        ]
        if any(p in link_text.lower() for p in skip_patterns):
            return None
        
        # Извлекаем данные из текста ссылки
        # Формат Kassir: "Название DD месяц HH:MM ДН" или "Название. ₽ от XXXX"
        
        # Название — текст до даты или до точки
        title = self._extract_title(link_text)
        if not title or len(title) < 3:
            return None
        
        # Дата
        date_start = self._extract_date(link_text)
        
        # Если не нашли дату в ссылке — ищем в родителе
        if not date_start:
            parent = link.find_parent(["div", "li", "article"])
            if parent:
                parent_text = parent.get_text(separator=" ")
                date_start = self._extract_date(parent_text)
        
        if not date_start:
            return None
        
        # Место
        location = self._extract_location(link, link_text)
        
        return EventData(
            title=title[:200],
            description=title,
            category="entertainment",
            date_start=date_start,
            location=location,
            source_url=event_url,
        )
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Извлечь название из текста карточки."""
        # Убираем дату, время, цену, возрастное ограничение
        
        # Ищем начало даты (DD месяц)
        date_match = re.search(
            r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|'
            r'августа|сентября|октября|ноября|декабря)',
            text, re.IGNORECASE
        )
        
        if date_match:
            title = text[:date_match.start()].strip()
        else:
            # Ищем начало числовой даты (DD, DD мая)
            num_date = re.search(r'\d{1,2}\s*,\s*\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)', text, re.IGNORECASE)
            if num_date:
                title = text[:num_date.start()].strip()
            else:
                # Убираем цену и возраст
                title = re.sub(r'[₽€$]\s*от\s*[\d\s]+', '', text)
                title = re.sub(r'\d+\+', '', title)
                title = title.strip(". ")
        
        # Убираем trailing мусор
        title = re.sub(r'[\.\s,]+$', '', title)
        title = title.strip()
        
        return title if title and len(title) >= 3 else None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Извлечь дату из текста."""
        # Паттерн: "DD месяц HH:MM" или "DD месяц"
        match = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|'
            r'августа|сентября|октября|ноября|декабря)'
            r'(?:[,\s]+(\d{1,2}):(\d{2}))?',
            text, re.IGNORECASE
        )
        
        if not match:
            return None
        
        day = int(match.group(1))
        month_name = match.group(2).lower()
        month = MONTHS_RU.get(month_name)
        
        if not month or day < 1 or day > 31:
            return None
        
        year = _guess_year(month)
        
        hour, minute = 19, 0
        if match.group(3) and match.group(4):
            h = int(match.group(3))
            m = int(match.group(4))
            if 0 <= h <= 23 and 0 <= m <= 59:
                hour, minute = h, m
        
        # Ищем время отдельно если не нашли рядом с датой
        if not match.group(3):
            time_match = re.search(r'(\d{1,2}):(\d{2})', text[match.end():match.end()+20])
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2))
                if 0 <= h <= 23 and 0 <= m <= 59:
                    hour, minute = h, m
        
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
    
    def _extract_location(self, link, link_text: str) -> str:
        """Извлечь место проведения."""
        # На Kassir место обычно в отдельной ссылке рядом
        parent = link.find_parent(["div", "li"])
        if parent:
            # Ищем ссылку на площадку
            venue_link = parent.find("a", href=re.compile(
                r"/(sportivnye-kompleksy|kluby|koncertnye-zaly|teatry|doma-kultury|muzei|drugoe)/"
            ))
            if venue_link:
                venue_text = self.clean_text(venue_link.get_text())
                if venue_text and len(venue_text) > 3:
                    return venue_text
        
        return "Нижний Новгород"
