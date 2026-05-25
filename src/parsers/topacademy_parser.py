"""Парсер Top Academy — мероприятия в IT-академии."""
import asyncio
import re
import urllib.request
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import _guess_year


class TopAcademyParser(BaseParser):
    """
    Парсер событий с nn.top-academy.ru/events.
    
    Сайт построен на Next.js (SSR). Использует HTTP/2 с keep-alive,
    что вызывает таймауты в aiohttp. Используем urllib через executor.
    """
    
    REQUEST_TIMEOUT = 30
    
    def __init__(self):
        super().__init__(
            source_name="Top Academy",
            source_url="https://nn.top-academy.ru/events"
        )
    
    async def fetch_html(self, url: str) -> str:
        """Загрузка через urllib (синхронно в executor) — обход проблем aiohttp с HTTP/2."""
        def _fetch():
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9",
                }
            )
            with urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
    
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
                    event = self._parse_card(article)
                    if event and event.source_url not in seen_urls:
                        seen_urls.add(event.source_url)
                        events.append(event)
                except Exception:
                    continue
        
        except Exception as e:
            print(f"  Error fetching Top Academy: {type(e).__name__}: {str(e)[:80]}")
        
        return events
    
    def _parse_card(self, card) -> Optional[EventData]:
        """Парсить одну карточку события."""
        title_elem = card.find(["h1", "h2", "h3", "h4"])
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        if not title or len(title) < 5:
            return None
        
        if title.lower() in ("все", "бесплатно", "события", "мероприятия"):
            return None
        
        link = card.find("a", href=True)
        href = "https://nn.top-academy.ru/events"
        if link:
            href_raw = link.get("href", "")
            if href_raw.startswith("http"):
                href = href_raw
            elif href_raw.startswith("/"):
                href = f"https://nn.top-academy.ru{href_raw}"
        
        slug = re.sub(r"[^a-zа-я0-9]+", "-", title.lower())[:60]
        if "/events/" not in href and "/event/" not in href:
            href = f"https://nn.top-academy.ru/events#{slug}"
        
        text = card.get_text(separator=" ", strip=True)
        date_start = self._extract_date(text)
        
        if not date_start:
            now = datetime.now()
            year = now.year + (1 if now.month >= 12 else 0)
            month = 1 if now.month >= 12 else now.month + 1
            date_start = datetime(year, month, 15, 10, 0)
        
        img = card.find("img")
        image_url = None
        if img:
            image_url = img.get("src") or img.get("data-src")
            if image_url and not image_url.startswith("http") and image_url.startswith("/"):
                image_url = f"https://nn.top-academy.ru{image_url}"
        
        return EventData(
            title=title[:500],
            description=title,
            category="it",
            date_start=date_start,
            location="Top Academy, Нижний Новгород",
            source_url=href[:1000],
            image_url=image_url,
        )
    
    def _extract_date(self, text: str) -> Optional[datetime]:
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
        
        time_match = re.search(r'(\d{1,2}):(\d{2})', text[match.end():match.end() + 50])
        hour, minute = 10, 0
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
