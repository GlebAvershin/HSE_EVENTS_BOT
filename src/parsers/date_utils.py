"""Утилиты для парсинга дат на русском языке."""
import re
from datetime import datetime, timedelta
from typing import Optional


# Русские месяцы
MONTHS_RU = {
    "января": 1, "янв": 1,
    "февраля": 2, "фев": 2,
    "марта": 3, "мар": 3,
    "апреля": 4, "апр": 4,
    "мая": 5,
    "июня": 6, "июн": 6,
    "июля": 7, "июл": 7,
    "августа": 8, "авг": 8,
    "сентября": 9, "сен": 9, "сент": 9,
    "октября": 10, "окт": 10,
    "ноября": 11, "ноя": 11,
    "декабря": 12, "дек": 12,
}

# Альтернативные формы (именительный падеж)
MONTHS_RU_NOM = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}

ALL_MONTHS = {**MONTHS_RU, **MONTHS_RU_NOM}


def parse_russian_date(date_str: str) -> Optional[datetime]:
    """
    Парсить дату из русскоязычной строки.
    
    Поддерживаемые форматы:
    - "15 апреля 2025"
    - "15 апреля 2025, 19:00"
    - "15 апр 19:00"
    - "15.04.2025"
    - "2025-04-15"
    - "2025-04-15T19:00:00"
    - "15 апреля"
    - "сегодня", "завтра"
    
    Args:
        date_str: Строка с датой
        
    Returns:
        datetime или None если не удалось распарсить
    """
    if not date_str:
        return None
    
    date_str_original = date_str.strip()
    date_str = date_str_original.lower()
    
    # Убираем лишние пробелы
    date_str = re.sub(r'\s+', ' ', date_str)
    
    # Сегодня/завтра
    if "сегодня" in date_str:
        time = _extract_time(date_str)
        result = datetime.now().replace(hour=time[0], minute=time[1], second=0, microsecond=0)
        return result
    
    if "завтра" in date_str:
        time = _extract_time(date_str)
        result = (datetime.now() + timedelta(days=1)).replace(
            hour=time[0], minute=time[1], second=0, microsecond=0
        )
        return result
    
    # ISO формат: 2025-04-15 или 2025-04-15T19:00:00 или 2025-04-15 19:00
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2})(?::(\d{2}))?)?', date_str_original, re.IGNORECASE)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        hour = int(iso_match.group(4)) if iso_match.group(4) else 0
        minute = int(iso_match.group(5)) if iso_match.group(5) else 0
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
    
    # Формат DD.MM.YYYY или DD.MM.YY
    dot_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', date_str)
    if dot_match:
        day = int(dot_match.group(1))
        month = int(dot_match.group(2))
        year = int(dot_match.group(3))
        if year < 100:
            year += 2000
        time = _extract_time(date_str)
        try:
            return datetime(year, month, day, time[0], time[1])
        except ValueError:
            return None
    
    # Формат DD.MM (без года)
    dot_no_year = re.search(r'(\d{1,2})\.(\d{1,2})(?!\.\d)', date_str)
    if dot_no_year:
        day = int(dot_no_year.group(1))
        month = int(dot_no_year.group(2))
        year = _guess_year(month, day)
        time = _extract_time(date_str)
        try:
            return datetime(year, month, day, time[0], time[1])
        except ValueError:
            return None
    
    # Русский формат: "15 апреля 2025" или "15 апреля" или "15 апр"
    for month_name, month_num in ALL_MONTHS.items():
        if month_name in date_str:
            # Ищем день перед названием месяца
            day_match = re.search(rf'(\d{{1,2}})\s*{re.escape(month_name)}', date_str)
            if day_match:
                day = int(day_match.group(1))
                
                # Ищем год
                year_match = re.search(r'(\d{4})', date_str)
                if year_match:
                    year = int(year_match.group(1))
                else:
                    year = _guess_year(month_num, day)
                
                time = _extract_time(date_str)
                try:
                    return datetime(year, month_num, day, time[0], time[1])
                except ValueError:
                    return None
    
    # Только время без даты — считаем сегодня
    time_only = re.search(r'^(\d{1,2}):(\d{2})$', date_str.strip())
    if time_only:
        hour = int(time_only.group(1))
        minute = int(time_only.group(2))
        now = datetime.now()
        try:
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            return None
    
    return None


def _extract_time(text: str) -> tuple:
    """
    Извлечь время из строки.
    
    Returns:
        (hour, minute) или (19, 0) по умолчанию
    """
    time_match = re.search(r'(\d{1,2}):(\d{2})', text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    return (19, 0)  # По умолчанию 19:00


def _guess_year(month: int, day: int = 1) -> int:
    """
    Угадать год для даты без года.
    
    Логика: если дата (месяц+день) уже прошла более 2 месяцев назад,
    считаем что это следующий год. Иначе — текущий.
    Это позволяет корректно обрабатывать недавно прошедшие события
    (не перебрасывая их на год вперёд).
    """
    now = datetime.now()
    try:
        candidate = datetime(now.year, month, day)
    except ValueError:
        # Невалидная дата (например 30 февраля)
        return now.year
    
    # Если дата прошла более 60 дней назад — скорее всего следующий год
    from datetime import timedelta
    if candidate < now - timedelta(days=60):
        return now.year + 1
    else:
        return now.year
