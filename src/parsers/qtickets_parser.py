"""Парсер QTickets для Нижнего Новгорода через headless-браузер."""
import asyncio
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from src.parsers.browser_parser import BrowserParser
from src.parsers.base import EventData
from src.parsers.date_utils import parse_russian_date, MONTHS_RU, _guess_year


class QTicketsParser(BrowserParser):
    """
    Парсер событий с QTickets через Playwright.
    
    QTickets — SPA, контент рендерится JavaScript'ом.
    """
    
    def __init__(self):
        super().__init__(
            source_name="QTickets",
            source_url="https://nnovgorod.qtickets.events/"
        )
    
    async def _parse_with_browser(self) -> List[EventData]:
        """Парсить события с QTickets."""
        html = await self.fetch_rendered_html(
            self.source_url,
            wait_selector="a[href*='nnovgorod.qtickets.events/']"
        )
        
        # Прокрутка для загрузки контента
        if self._browser:
            page = await self._browser.new_page()
            try:
                await page.goto(self.source_url, timeout=self.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=self.NETWORK_IDLE_TIMEOUT)
                await asyncio.sleep(2)
                # Прокрутка вниз для загрузки ленивого контента
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(3)
                html = await page.content()
            finally:
                await page.close()
        
        return self._extract_events(html)
    
    def _extract_events(self, html: str) -> List[EventData]:
        """Извлечь события из отрендеренного HTML."""
        events = []
        soup = BeautifulSoup(html, "html.parser")
        
        # QTickets: ссылки формата https://nnovgorod.qtickets.events/NNNNNN-slug
        event_links = soup.find_all("a", href=re.compile(
            r"nnovgorod\.qtickets\.events/\d+"
        ))
        
        seen_urls = set()
        for link in event_links:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"https://{href}"
            
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            try:
                event = self._parse_event_link(link, href)
                if event:
                    events.append(event)
            except Exception:
                continue
        
        return events[:20]
    
    def _parse_event_link(self, link, event_url: str) -> Optional[EventData]:
        """Парсить одну ссылку на событие."""
        # Получаем текст ссылки
        link_text = link.get_text(separator=" ")
        link_text = self.clean_text(link_text)
        
        if not link_text or len(link_text) < 5:
            return None
        
        # Формат QTickets: "Купить билет от XXX руб. НАЗВАНИЕ Категория Дата Место"
        # Убираем "Купить билет" и цену
        title = re.sub(r'Купить\s*билет\s*', '', link_text, flags=re.IGNORECASE)
        title = re.sub(r'от\s*\d[\d\s]*руб\.?', '', title)
        title = re.sub(r'Сегодня|Завтра', '', title, flags=re.IGNORECASE)
        
        # Убираем категорию (Концерт, Шоу, Спорт и т.д.) и дату/время/место в конце
        # Паттерн: "НАЗВАНИЕ Категория DD месяц, HH:MM | Место"
        title = re.sub(
            r'\s+(Концерт|Шоу|Спорт|Фестиваль|Выставка|Театр|Детям)\s+\d{1,2}\s+'
            r'(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря).*$',
            '', title, flags=re.IGNORECASE
        )
        # Убираем оставшиеся даты
        title = re.sub(
            r'\s+\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря).*$',
            '', title, flags=re.IGNORECASE
        )
        title = title.strip()
        
        if not title or len(title) < 3:
            return None
        
        # Дата — ищем в тексте или в родителе
        parent = link.find_parent(["div", "article", "li"])
        search_text = (parent.get_text(separator=" ") if parent else link_text)
        
        date_start = None
        date_match = re.search(
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|'
            r'августа|сентября|октября|ноября|декабря)',
            search_text, re.IGNORECASE
        )
        if date_match:
            date_str = date_match.group(0)
            time_match = re.search(r'(\d{1,2}):(\d{2})', search_text)
            if time_match:
                date_str += f" {time_match.group(0)}"
            date_start = parse_russian_date(date_str)
        
        # Если "Сегодня" в тексте
        if not date_start and "сегодня" in link_text.lower():
            from datetime import timedelta
            date_start = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        
        if not date_start:
            # Без даты — пропускаем, но для QTickets можно взять из URL slug
            return None
        
        # Место
        location = "Нижний Новгород"
        if parent:
            location_elem = parent.find(class_=re.compile(r"place|venue|location", re.I))
            if location_elem:
                loc_text = self.clean_text(location_elem.get_text())
                if loc_text and len(loc_text) > 3:
                    # Убираем дату/время из location если попало
                    loc_text = re.sub(
                        r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|'
                        r'августа|сентября|октября|ноября|декабря)[,\s]*\d{0,2}:?\d{0,2}\s*\|?\s*',
                        '', loc_text, flags=re.IGNORECASE
                    ).strip()
                    if loc_text:
                        location = loc_text
        
        return EventData(
            title=title[:200],
            description=title,
            category="entertainment",
            date_start=date_start,
            location=location,
            source_url=event_url,
        )
