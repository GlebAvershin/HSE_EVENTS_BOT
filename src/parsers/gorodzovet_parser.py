"""Парсер Gorodzovet — IT-мероприятия в Нижнем Новгороде."""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import _guess_year


class GorodzovetParser(BaseParser):
    """
    Парсер событий с gorodzovet.ru.
    
    Структура: ссылки вида /nnovgorod/<slug>-event<ID>
    """
    
    REQUEST_TIMEOUT = 25  # сайт медленный
    
    def __init__(self):
        super().__init__(
            source_name="Gorodzovet",
            source_url="https://gorodzovet.ru/nnovgorod/it/"
        )
    
    async def parse(self) -> List[EventData]:
        """Парсить события."""
        events = []
        
        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)
            
            # Уникальные ссылки на события
            event_links = soup.find_all("a", href=re.compile(r"-event\d+"))
            seen_urls = set()
            
            for link in event_links:
                try:
                    event = self._parse_link(link)
                    if event and event.source_url not in seen_urls:
                        seen_urls.add(event.source_url)
                        events.append(event)
                except Exception:
                    continue
        
        except Exception as e:
            print(f"  Error fetching Gorodzovet: {type(e).__name__}: {str(e)[:80]}")
        
        return events
    
    def _parse_link(self, link) -> Optional[EventData]:
        """Парсить ссылку на событие."""
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https://gorodzovet.ru{href}"
        href = href.split("?")[0].split("#")[0]
        
        title = self.clean_text(link.get_text(separator=" "))
        if not title or len(title) < 5:
            return None
        
        # Очищаем заголовок от навигационных слов
        title = re.sub(r'^(Подробнее|Афиша|Купить билет)[\s:]*', '', title, flags=re.I).strip()
        
        # Дата может быть рядом в родителе
        parent = link.find_parent(["div", "li", "article"])
        date_start = None
        if parent:
            parent_text = parent.get_text(separator=" ", strip=True)
            date_start = self._extract_date(parent_text)
        
        if not date_start:
            # Если нет даты — ставим на следующий месяц
            now = datetime.now()
            year = now.year + (1 if now.month == 12 else 0)
            month = 1 if now.month == 12 else now.month + 1
            date_start = datetime(year, month, 15, 19, 0)
        
        return EventData(
            title=title[:500],
            description=title,
            category="it",
            date_start=date_start,
            location="Нижний Новгород",
            source_url=href,
        )
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Извлечь дату из текста."""
        # Формат "DD месяц"
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
        
        # Время рядом
        time_match = re.search(r'(\d{1,2}):(\d{2})', text[match.end():match.end() + 30])
        hour, minute = 19, 0
        if time_match:
            h, m = int(time_match.group(1)), int(time_match.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                hour, minute = h, m
        
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
