"""Парсер Habr Events — IT-конференции и митапы.

Habr Events отдаёт серверный HTML с карточками событий.
Структура: div.tm-event-card с датой, названием, городом и категорией.

Парсим только события с городом "Нижний Новгород" или "Онлайн".
"""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import parse_russian_date


class HabrEventsParser(BaseParser):
    """
    Парсер IT-событий с Habr Events.
    
    Фильтрует по городам: Нижний Новгород и Онлайн.
    """
    
    # Города, которые нас интересуют
    ALLOWED_CITIES = {"нижний новгород", "онлайн", "online", ""}
    
    def __init__(self):
        super().__init__(
            source_name="Habr Events",
            source_url="https://habr.com/ru/events/"
        )
    
    async def parse(self) -> List[EventData]:
        """Парсить IT-события с Habr."""
        events = []
        
        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)
            
            # Карточки событий: div.tm-event-card (не img, не wrapper)
            cards = soup.find_all("div", class_="tm-event-card__info")
            
            for card in cards[:30]:
                try:
                    event = self._parse_card(card)
                    if event:
                        events.append(event)
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"Error fetching Habr Events: {e}")
        
        return events
    
    def _parse_card(self, card) -> Optional[EventData]:
        """Парсить карточку события."""
        # Структура текста: "Дата | Название | Город1 • Город2"
        card_text = card.get_text(separator="|", strip=True)
        parts = [p.strip() for p in card_text.split("|") if p.strip()]
        
        if len(parts) < 3:
            return None
        
        # Город — третий и далее элементы (кроме "•")
        cities = [p.lower() for p in parts[2:] if p != "•"]
        
        # Фильтруем: только НН или Онлайн
        is_nn = any("нижний новгород" in c for c in cities)
        is_online = any("онлайн" in c or "online" in c for c in cities)
        
        if not is_nn and not is_online:
            return None
        
        # Название
        title_link = card.find("a", class_=re.compile(r"title", re.I))
        if not title_link:
            title_link = card.find("a", href=re.compile(r"/events/\d+"))
        
        if not title_link:
            return None
        
        title = self.clean_text(title_link.get_text())
        if not title or len(title) < 3:
            return None
        
        # URL
        href = title_link.get("href", "")
        if not href.startswith("http"):
            event_url = f"https://habr.com{href}"
        else:
            event_url = href
        
        # Дата — первый элемент
        date_start = self._extract_date(parts[0])
        if not date_start:
            return None
        
        # Место
        location = "Нижний Новгород" if is_nn else "Онлайн"
        
        return EventData(
            title=title[:500],
            description=title,
            category="it",
            date_start=date_start,
            location=location,
            source_url=event_url,
        )
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Извлечь дату из текста карточки."""
        # Формат Habr: "2 марта – 10 августа" или "19 мая"
        match = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|'
            r'августа|сентября|октября|ноября|декабря)',
            text, re.IGNORECASE
        )
        if match:
            return parse_russian_date(match.group(0))
        return None
