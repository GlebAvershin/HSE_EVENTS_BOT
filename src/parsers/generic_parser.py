"""Универсальный парсер для различных источников событий.

Этот парсер пытается извлечь события из произвольных HTML-страниц.
Работает только с сайтами, которые отдают серверный HTML (не SPA).

Если сайт не отдаёт контент или структура не распознана,
парсер вернёт пустой список без ошибки.
"""
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import parse_russian_date


class GenericEventParser(BaseParser):
    """Универсальный парсер событий для серверных HTML-страниц."""
    
    # Минимальная длина HTML для считания страницы "непустой"
    MIN_HTML_LENGTH = 1000
    
    # Минимальное количество событий для считания парсинга успешным
    MIN_EVENTS_THRESHOLD = 1
    
    def __init__(self, source_name: str, source_url: str, default_category: str = "it"):
        super().__init__(source_name, source_url)
        self.default_category = default_category
    
    async def fetch_html_safe(self, url: str) -> str:
        """Fetch HTML с обработкой разных кодировок."""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        import asyncio
        import aiohttp
        
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    raw_bytes = await response.read()
                    # Пробуем utf-8, потом windows-1251
                    try:
                        return raw_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            return raw_bytes.decode("windows-1251")
                        except UnicodeDecodeError:
                            return raw_bytes.decode("utf-8", errors="replace")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    import asyncio as aio
                    await aio.sleep(self.RETRY_DELAY * (attempt + 1))
        
        raise last_error
    
    async def parse(self) -> List[EventData]:
        """Парсить события из источника."""
        events = []
        
        try:
            html = await self.fetch_html_safe(self.source_url)
            
            # Проверяем что страница не пустая (SPA-сайты отдают мало контента)
            if len(html) < self.MIN_HTML_LENGTH:
                print(f"  [SKIP] {self.source_name}: page too short ({len(html)} bytes), likely SPA")
                return []
            
            soup = self.parse_html(html)
            
            # Проверяем что на странице есть текстовый контент
            text_content = soup.get_text(strip=True)
            if len(text_content) < 200:
                print(f"  [SKIP] {self.source_name}: no meaningful text content, likely SPA")
                return []
            
            # Стратегия 1: ищем карточки событий по семантическим классам
            event_cards = self._find_event_cards(soup)
            
            for card in event_cards[:20]:
                try:
                    event = self._parse_event_card(card)
                    if event:
                        events.append(event)
                except Exception:
                    continue
            
            if not events:
                print(f"  [WARN] {self.source_name}: HTML received but no events extracted")
        
        except Exception as e:
            error_type = type(e).__name__
            print(f"  [ERROR] {self.source_name}: {error_type}: {str(e)[:100]}")
        
        return events
    
    def _find_event_cards(self, soup) -> list:
        """Найти карточки событий на странице."""
        # Приоритетные селекторы
        selectors = [
            ("article", {"class_": re.compile(r"event", re.I)}),
            ("div", {"class_": re.compile(r"event[-_]card|event[-_]item|eventCard", re.I)}),
            ("div", {"class_": re.compile(r"^event$", re.I)}),
            ("a", {"href": re.compile(r"/event[s]?/")}),
            ("div", {"class_": re.compile(r"card", re.I)}),
        ]
        
        for tag, attrs in selectors:
            cards = soup.find_all(tag, **attrs)
            if len(cards) >= 2:
                return cards
        
        return []
    
    def _parse_event_card(self, card) -> Optional[EventData]:
        """Парсить карточку события."""
        # Название — обязательно
        title = self._extract_title(card)
        if not title or len(title) < 3:
            return None
        
        # URL — обязательно
        event_url = self._extract_url(card)
        if not event_url:
            return None
        
        # Дата — пытаемся извлечь реальную
        date_start = self._extract_date(card)
        if not date_start:
            # Без даты событие бесполезно
            return None
        
        # Место
        location = self._extract_location(card)
        
        # Описание
        description = self._extract_description(card, title)
        
        # Категория
        category = self._determine_category(title, description)
        
        return EventData(
            title=title[:500],
            description=description[:500],
            category=category,
            date_start=date_start,
            location=location,
            source_url=event_url,
            image_url=self._extract_image(card),
        )
    
    def _extract_title(self, card) -> Optional[str]:
        """Извлечь название события."""
        for tag in ("h1", "h2", "h3", "h4"):
            elem = card.find(tag)
            if elem:
                text = self.clean_text(elem.get_text())
                if text and len(text) >= 3:
                    return text
        
        # По классу
        elem = card.find(class_=re.compile(r"title|name", re.I))
        if elem:
            text = self.clean_text(elem.get_text())
            if text and len(text) >= 3:
                return text
        
        # Из ссылки
        link = card.find("a")
        if link:
            text = self.clean_text(link.get_text())
            if text and len(text) >= 3:
                return text
        
        return None
    
    def _extract_url(self, card) -> Optional[str]:
        """Извлечь URL события."""
        link = card.find("a", href=True)
        if not link:
            if card.name == "a" and card.get("href"):
                link = card
            else:
                return None
        
        url = link["href"]
        if not url or url == "#":
            return None
        
        if not url.startswith("http"):
            parsed = urlparse(self.source_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            if url.startswith("/"):
                url = f"{base}{url}"
            else:
                url = f"{base}/{url}"
        
        return url
    
    def _extract_date(self, card) -> Optional[datetime]:
        """Извлечь дату события."""
        # Ищем элемент <time> с datetime атрибутом
        time_elem = card.find("time")
        if time_elem:
            dt_attr = time_elem.get("datetime")
            if dt_attr:
                parsed = parse_russian_date(dt_attr)
                if parsed:
                    return parsed
            # Текст элемента time
            parsed = parse_russian_date(time_elem.get_text())
            if parsed:
                return parsed
        
        # Ищем по классу date/time
        date_elem = card.find(class_=re.compile(r"date|time|когда", re.I))
        if date_elem:
            parsed = parse_russian_date(date_elem.get_text())
            if parsed:
                return parsed
        
        # Ищем дату в тексте карточки
        card_text = card.get_text()
        
        # Паттерн: "DD месяц YYYY" или "DD месяц"
        date_pattern = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|'
            r'августа|сентября|октября|ноября|декабря)(?:\s+(\d{4}))?',
            card_text, re.IGNORECASE
        )
        if date_pattern:
            parsed = parse_russian_date(date_pattern.group(0))
            if parsed:
                return parsed
        
        # Паттерн: DD.MM.YYYY
        dot_pattern = re.search(r'\d{1,2}\.\d{1,2}\.\d{2,4}', card_text)
        if dot_pattern:
            parsed = parse_russian_date(dot_pattern.group(0))
            if parsed:
                return parsed
        
        return None
    
    def _extract_location(self, card) -> str:
        """Извлечь место проведения."""
        elem = card.find(class_=re.compile(r"place|venue|location|address|город", re.I))
        if elem:
            text = self.clean_text(elem.get_text())
            if text and len(text) > 3:
                return text[:200]
        return "Нижний Новгород"
    
    def _extract_description(self, card, title: str) -> str:
        """Извлечь описание."""
        desc_elem = card.find("p")
        if not desc_elem:
            desc_elem = card.find(class_=re.compile(r"desc|text|content|body", re.I))
        
        if desc_elem:
            text = self.clean_text(desc_elem.get_text())
            if text and text != title and len(text) > 10:
                return text[:500]
        
        return title
    
    def _extract_image(self, card) -> Optional[str]:
        """Извлечь URL изображения."""
        img = card.find("img")
        if not img:
            return None
        
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            return None
        
        if not src.startswith("http"):
            parsed = urlparse(self.source_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            src = f"{base}{src}" if src.startswith("/") else f"{base}/{src}"
        
        return src
    
    def _determine_category(self, title: str, description: str) -> str:
        """Определить категорию по контенту."""
        if self.default_category:
            return self.default_category
        text = f"{title} {description}".lower()
        return self.normalize_category(text)
