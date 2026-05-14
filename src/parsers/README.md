# Парсеры событий

Модуль для автоматического сбора событий из различных источников.

## Источники

1. **Яндекс.Афиша** - концерты, театр, выставки
2. **IT52.info** - IT события Нижнего Новгорода
3. **Networkly** - IT события и нетворкинг
4. **All-Events** - IT мероприятия
5. **Timepad** - IT и интернет события
6. **Top Academy** - образовательные IT события
7. **Gorodzovet** - IT события города
8. **Yandex Dev** - события для разработчиков

## Использование

### Ручной запуск парсинга

```bash
python run_parser.py
```

### Через админ-команду в боте

```
/admin_parse
```

Доступно только для администраторов.

## Архитектура

- `base.py` - базовый класс для всех парсеров
- `yandex_afisha.py` - парсер Яндекс.Афиши
- `it52_parser.py` - парсер IT52.info
- `generic_parser.py` - универсальный парсер для остальных источников
- `parser_manager.py` - менеджер для управления всеми парсерами
- `scheduler.py` - планировщик автоматического парсинга

## Как работает

1. Каждый парсер наследуется от `BaseParser`
2. Реализует метод `parse()` который возвращает список `EventData`
3. `ParserManager` запускает все парсеры и сохраняет события в БД
4. Проверяются дубликаты по `source_url`
5. Категория определяется автоматически по ключевым словам

## Добавление нового парсера

```python
from src.parsers.base import BaseParser, EventData

class MyParser(BaseParser):
    def __init__(self):
        super().__init__("My Source", "https://example.com")
    
    async def parse(self) -> List[EventData]:
        html = await self.fetch_html(self.source_url)
        soup = self.parse_html(html)
        
        # Парсинг...
        
        return events
```

Затем добавить в `parser_manager.py`:

```python
self.parsers = [
    # ...
    MyParser(),
]
```

## Автоматический парсинг

Парсинг запускается автоматически каждые 6 часов (настраивается в `scheduler.py`).

Для включения автоматического парсинга добавьте в `src/bot/main.py`:

```python
from src.parsers.scheduler import parsing_scheduler

async def on_startup(bot: Bot):
    # ...
    parsing_scheduler.start(interval_hours=6)

async def on_shutdown(bot: Bot):
    # ...
    parsing_scheduler.stop()
```

## Примечания

- Парсеры используют `aiohttp` для асинхронных запросов
- HTML парсится с помощью `BeautifulSoup` и `lxml`
- Даты пока устанавливаются на +7 дней (требуется доработка парсинга дат)
- Категория определяется по ключевым словам в названии/описании
