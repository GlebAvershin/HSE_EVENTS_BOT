"""Парсер All-Events.ru — IT-мероприятия в Нижнем Новгороде."""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import _guess_year


class AllEventsParser(BaseParser):
    """
    Парсер событий с all-events.ru.
    
    Структура: ссылки на /events/<slug>/ — каждое событие имеет несколько ссылок
    (обычно 4: регистрация, картинка, заголовок, ещё одна).
    """
    
    REQUEST_TIMEOUT = 25
    
    def __init__(self):
        super().__init__(
            source_name="All-Events",
            source_url="https://all-events.ru/events/calendar/city-is-nizhniy_novgorod/theme-is-informatsionnye_tekhnologii/tags-is-digital/"
        )
    
    async def parse(self) -> List[EventData]:
        """Парсить события."""
        events = []
        
        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)
            
            # Все ссылки на события (исключая calendar/)
            event_links = soup.find_all("a", href=re.compile(r"^/events/(?!calendar/)[a-z0-9_\-]+/?$"))
            
            # Группируем по slug, оставляя ту, у которой есть текст
            slug_to_event = {}
            for link in event_links:
                href = link.get("href", "")
                slug_match = re.match(r"/events/([a-z0-9_\-]+)/?", href)
                if not slug_match:
                    continue
                slug = slug_match.group(1)
                
                text = self.clean_text(link.get_text())
                # Пропускаем "Регистрация" и пустые
                if not text or text.lower() in ("регистрация", "подробнее", "купить билет"):
                    if slug not in slug_to_event:
                        slug_to_event[slug] = (None, link)
                    continue
                
                # Сохраняем ссылку с заголовком
                slug_to_event[slug] = (text, link)
            
            for slug, (title, link) in slug_to_event.items():
                if not title or len(title) < 5:
                    continue
                
                try:
                    event = self._build_event(slug, title, link)
                    if event:
                        events.append(event)
                except Exception:
                    continue
        
        except Exception as e:
            print(f"  Error fetching All-Events: {type(e).__name__}: {str(e)[:80]}")
        
        return events
    
    def _build_event(self, slug: str, title: str, link) -> Optional[EventData]:
        """Построить событие из заголовка и контекста."""
        href = f"https://all-events.ru/events/{slug}/"
        
        # Ищем дату в родителе
        date_start = None
        for ancestor in link.find_parents(["div", "article", "li"])[:3]:
            text = ancestor.get_text(separator=" ", strip=True)
            if len(text) > 5000:
                # Слишком большой контекст — это вся страница
                continue
            date_start = self._extract_date(text)
            if date_start:
                break
        
        if not date_start:
            # Если нет даты — ставим на следующий месяц
            now = datetime.now()
            year = now.year + (1 if now.month == 12 else 0)
            month = 1 if now.month == 12 else now.month + 1
            date_start = datetime(year, month, 15, 10, 0)
        
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
        match = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s*(\d{4})?',
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
        
        year_str = match.group(3)
        year = int(year_str) if year_str else _guess_year(month)
        
        try:
            dt = datetime(year, month, day, 10, 0)
            if dt < datetime.now():
                return None
            return dt
        except ValueError:
            return None
