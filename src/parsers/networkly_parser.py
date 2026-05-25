"""Парсер Networkly.app — IT-мероприятия в Нижнем Новгороде."""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import MONTHS_RU, _guess_year


class NetworklyParser(BaseParser):
    """
    Парсер событий с Networkly.app.
    
    Networkly — платформа для IT-мероприятий.
    Структура: <article> с заголовком, ссылкой, датой и описанием.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Networkly",
            source_url="https://networkly.app/event?event_filter%5Bcity_id%5D%5B%5D=520555"
        )
    
    async def parse(self) -> List[EventData]:
        """Парсить события."""
        events = []
        
        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)
            
            articles = soup.find_all("article")
            seen_urls = set()
            
            for article in articles[:30]:
                try:
                    event = self._parse_article(article)
                    if event and event.source_url not in seen_urls:
                        seen_urls.add(event.source_url)
                        events.append(event)
                except Exception:
                    continue
        
        except Exception as e:
            print(f"  Error fetching Networkly: {type(e).__name__}: {str(e)[:80]}")
        
        return events
    
    def _parse_article(self, article) -> Optional[EventData]:
        """Парсить одну карточку события."""
        # Ссылка на событие
        link = article.find("a", href=re.compile(r"/event/[a-z0-9\-]"))
        if not link:
            return None
        
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https://networkly.app{href}"
        
        # Заголовок
        title_elem = article.find(["h1", "h2", "h3", "h4"])
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        if not title or len(title) < 3:
            return None
        
        # Текст карточки для извлечения даты и места
        text = article.get_text(separator=" ", strip=True)
        
        # Пропускаем прошедшие события
        if "Мероприятие прошло" in text:
            return None
        
        # Извлекаем дату
        date_start = self._extract_date(text)
        if not date_start:
            return None
        
        # Место
        location = self._extract_location(text)
        
        # Изображение
        img = article.find("img")
        image_url = None
        if img:
            image_url = img.get("src") or img.get("data-src")
            if image_url and not image_url.startswith("http"):
                image_url = f"https://networkly.app{image_url}"
        
        return EventData(
            title=title[:500],
            description=title,
            category="it",
            date_start=date_start,
            location=location,
            source_url=href,
            image_url=image_url,
        )
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """
        Извлечь дату из текста.
        Формат: "пн, 25 май 2026, 16:00 (+00:00)" или "ср, 20 май 2026, 16:30"
        """
        # Полная дата: "DD месяц YYYY, HH:MM"
        full_match = re.search(
            r'(\d{1,2})\s+(янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)[а-я]*\s*(\d{4})?[\s,]+(\d{1,2}):(\d{2})',
            text, re.IGNORECASE
        )
        if not full_match:
            return None
        
        day = int(full_match.group(1))
        month_short = full_match.group(2).lower()
        year_str = full_match.group(3)
        hour = int(full_match.group(4))
        minute = int(full_match.group(5))
        
        # Маппинг коротких названий месяцев
        month_map = {
            "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
            "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
        }
        month = month_map.get(month_short)
        if not month:
            return None
        
        year = int(year_str) if year_str else _guess_year(month)
        
        try:
            dt = datetime(year, month, day, hour, minute)
            if dt < datetime.now():
                return None
            return dt
        except ValueError:
            return None
    
    def _extract_location(self, text: str) -> str:
        """Извлечь место проведения."""
        # На Networkly формат: "Нижний Новгород, Россия"
        if "Нижний Новгород" in text:
            return "Нижний Новгород"
        return "Нижний Новгород"
