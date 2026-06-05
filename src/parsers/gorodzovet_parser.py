"""Парсер Gorodzovet — городская афиша Нижнего Новгорода (IT и развлечения)."""
import re
from datetime import datetime
from typing import List, Optional

from src.parsers.base import BaseParser, EventData
from src.parsers.date_utils import _guess_year


# Ключевые слова для классификации события как IT.
# На gorodzovet нет отдельной IT-категории, поэтому категорию
# определяем по заголовку: совпадение -> 'it', иначе -> 'entertainment'.
IT_KEYWORDS = [
    "it", "айти", "митап", "meetup", "хакатон", "hackathon",
    "конференц", "программирован", "разработк", "developer",
    "tech", "технолог", "digital", "data", "python", "java",
    "frontend", "backend", "devops", "qa", "тестирован",
    "стартап", "startup", "fintech", "финтех", "блокчейн",
    "искусственный интеллект", "machine learning", "нейросет",
    "интерфейс", "nnfrontend", "nninterface",
]


class GorodzovetParser(BaseParser):
    """
    Парсер событий с gorodzovet.ru — общегородская афиша НН.

    На сайте нет рабочей IT-категории (путь /it/ молча отдаёт общую афишу),
    поэтому парсим общий список и классифицируем каждое событие по заголовку:
    IT-мероприятия -> 'it', всё остальное -> 'entertainment'.

    Структура ссылок: /nnovgorod/<slug>-event<ID>
    """

    REQUEST_TIMEOUT = 25  # сайт медленный

    def __init__(self):
        super().__init__(
            source_name="Gorodzovet",
            source_url="https://gorodzovet.ru/nnovgorod/"
        )

    async def parse(self) -> List[EventData]:
        """Парсить события."""
        events = []

        try:
            html = await self.fetch_html(self.source_url)
            soup = self.parse_html(html)

            # Ссылки на события НН: /nnovgorod/<slug>-event<ID>
            event_links = soup.find_all("a", href=re.compile(r"/nnovgorod/[a-z0-9\-]+-event\d+"))
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

        if not title or len(title) < 5:
            return None

        # Классифицируем по ключевым словам в заголовке (не отсеиваем!)
        title_lower = title.lower()
        category = "it" if any(kw in title_lower for kw in IT_KEYWORDS) else "entertainment"

        # Дата лежит в карточке-предке (event-block: "Июн 17").
        # Поднимаемся по родителям, пока не найдём распознаваемую дату.
        date_start = None
        node = link
        for _ in range(4):
            node = node.find_parent(["div", "li", "article", "section"])
            if not node:
                break
            date_start = self._extract_date(node.get_text(separator=" ", strip=True))
            if date_start:
                break

        if not date_start:
            # Если нет даты — ставим на следующий месяц
            now = datetime.now()
            year = now.year + (1 if now.month == 12 else 0)
            month = 1 if now.month == 12 else now.month + 1
            date_start = datetime(year, month, 15, 19, 0)

        return EventData(
            title=title[:500],
            description=title,
            category=category,
            date_start=date_start,
            location="Нижний Новгород",
            source_url=href,
        )
    
    # Месяц по первым 3 буквам названия (покрывает и сокращённую "Июн",
    # и полную форму "июня"/"марта"; "мая"/"мае" обрабатываются отдельно).
    _MONTHS = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "мая": 5, "мае": 5,
        "июн": 6, "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
    }

    def _month_num(self, token: str) -> Optional[int]:
        """Номер месяца по русскому названию (полному или сокращённому)."""
        return self._MONTHS.get(token.lower()[:3])

    def _extract_date(self, text: str) -> Optional[datetime]:
        """
        Извлечь дату из текста карточки.

        Поддерживает оба формата gorodzovet:
        - "Июн 17"  (сокращённый месяц + день)
        - "17 июня" (день + полный месяц)
        """
        day = month = None
        _MON = r'(янв|фев|мар|апр|ма[йяе]|июн|июл|авг|сен|окт|ноя|дек)'

        # Формат "DD месяц" ("17 июня") — проверяем первым, чтобы в строке
        # "17 июня 18:30" день не перепутался с часом времени.
        m = re.search(rf'\b(\d{{1,2}})\s+{_MON}[а-я]*', text, re.IGNORECASE)
        if m:
            day = int(m.group(1))
            month = self._month_num(m.group(2))
            tail_start = m.end()
        else:
            # Формат "Месяц DD" (на сайте: "Июн 17", "ИЮН 07").
            # (?!\s*:) — чтобы не принять час времени ("Июн 18:30") за день.
            m = re.search(rf'\b{_MON}[а-я]*\.?\s+(\d{{1,2}})\b(?!\s*:)', text, re.IGNORECASE)
            if m:
                month = self._month_num(m.group(1))
                day = int(m.group(2))
                tail_start = m.end()

        if not month or not day or not (1 <= day <= 31):
            return None

        year = _guess_year(month)

        # Время рядом (если указано)
        hour, minute = 19, 0
        time_match = re.search(r'(\d{1,2}):(\d{2})', text[tail_start:tail_start + 30])
        if time_match:
            h, mnt = int(time_match.group(1)), int(time_match.group(2))
            if 0 <= h <= 23 and 0 <= mnt <= 59:
                hour, minute = h, mnt

        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
