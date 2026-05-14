"""Парсер IT52.info - IT события Нижнего Новгорода через Atom feed."""
import re
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import parse_russian_date


class IT52Parser(BaseParser):
    """
    Парсер событий с IT52.info через Atom feed.
    
    IT52 предоставляет Atom feed по адресу /events.atom с полной информацией
    о предстоящих IT-событиях в Нижнем Новгороде.
    
    Структура feed:
    - entry/title — название
    - entry/link[@href] — URL события  
    - entry/content — HTML описание
    - entry/published — дата публикации (ISO)
    - URL содержит дату: /events/2026-05-12-название
    """
    
    ATOM_NS = "{http://www.w3.org/2005/Atom}"
    
    def __init__(self):
        super().__init__(
            source_name="IT52.info",
            source_url="https://www.it52.info/events.atom"
        )
    
    async def parse(self) -> List[EventData]:
        """Парсить события с IT52.info через Atom feed."""
        events = []
        
        try:
            xml_text = await self.fetch_html(self.source_url)
            
            # Парсим XML
            root = ElementTree.fromstring(xml_text)
            
            entries = root.findall(f"{self.ATOM_NS}entry")
            
            for entry in entries[:20]:
                try:
                    event = self._parse_entry(entry)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"  Error parsing IT52 entry: {e}")
                    continue
        
        except Exception as e:
            print(f"Error fetching IT52 Atom feed: {e}")
        
        return events
    
    def _parse_entry(self, entry: ElementTree.Element) -> Optional[EventData]:
        """Парсить одну запись из Atom feed."""
        # Название
        title_elem = entry.find(f"{self.ATOM_NS}title")
        if title_elem is None or not title_elem.text:
            return None
        title = self.clean_text(title_elem.text)
        
        # URL
        link_elem = entry.find(f"{self.ATOM_NS}link")
        if link_elem is None:
            return None
        event_url = link_elem.get("href", "")
        if not event_url:
            return None
        
        # Дата из URL: /events/2026-05-12-название
        date_start = self._extract_date_from_url(event_url)
        
        # Если не нашли в URL, пробуем published/updated
        if not date_start:
            published = entry.find(f"{self.ATOM_NS}published")
            if published is not None and published.text:
                date_start = self._parse_iso_date(published.text)
        
        if not date_start:
            updated = entry.find(f"{self.ATOM_NS}updated")
            if updated is not None and updated.text:
                date_start = self._parse_iso_date(updated.text)
        
        if not date_start:
            return None
        
        # Описание из content
        content_elem = entry.find(f"{self.ATOM_NS}content")
        description = title
        location = "Нижний Новгород"
        
        if content_elem is not None and content_elem.text:
            # Content может быть HTML — извлекаем текст
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content_elem.text, "html.parser")
            
            # Ищем адрес (обычно в ссылке на maps.yandex)
            map_link = soup.find("a", href=re.compile(r"maps\.yandex"))
            if map_link:
                location = self.clean_text(map_link.get_text())
            
            # Ищем время в тексте
            text_content = soup.get_text()
            time_match = re.search(r'(\d{1,2}):(\d{2})', text_content)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                if 0 <= hour <= 23:
                    date_start = date_start.replace(hour=hour, minute=minute)
            
            # Описание — первые 500 символов текста
            desc_text = self.clean_text(text_content)
            if desc_text and len(desc_text) > 10:
                description = desc_text[:500]
        
        return EventData(
            title=title,
            description=description,
            category="it",
            date_start=date_start,
            location=location,
            source_url=event_url,
        )
    
    def _extract_date_from_url(self, url: str) -> Optional[datetime]:
        """Извлечь дату из URL вида /events/2026-05-12-название."""
        match = re.search(r"/events/(\d{4})-(\d{2})-(\d{2})", url)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day, 19, 0)  # По умолчанию 19:00
            except ValueError:
                return None
        return None
    
    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """Парсить ISO дату."""
        try:
            # Убираем timezone info для простоты
            date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
            date_str = date_str.replace('Z', '')
            
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        return None
