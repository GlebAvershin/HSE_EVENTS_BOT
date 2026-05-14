"""Менеджер парсеров - управление всеми парсерами."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.parsers.base import EventData
from src.parsers.it52_parser import IT52Parser
from src.parsers.milo_parser import MiloParser
from src.parsers.kudago_parser import KudaGoParser
from src.parsers.habr_parser import HabrEventsParser
from src.parsers.kassir_parser import KassirParser
from src.parsers.qtickets_parser import QTicketsParser
from src.database.repositories.event import EventRepository


class ParserManager:
    """Менеджер для управления всеми парсерами."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация менеджера.
        
        Args:
            session: Сессия базы данных
        """
        self.session = session
        self.event_repo = EventRepository(session)
        
        # Парсеры разделены на два типа:
        # 1. Лёгкие (HTTP-only) — быстрые, без зависимостей
        # 2. Тяжёлые (Browser) — требуют Playwright + Chromium
        
        self.http_parsers = [
            IT52Parser(),         # Atom feed, IT-события НН
            MiloParser(),         # HTML (windows-1251), концерты НН
            KudaGoParser(),       # REST API, все категории НН (без авторизации)
            HabrEventsParser(),   # HTML, IT-конференции (НН + онлайн)
        ]
        
        self.browser_parsers = [
            KassirParser(),        # SPA, концерты/шоу (30+ событий)
            QTicketsParser(),      # SPA, развлечения (18+ событий)
        ]
    
    async def parse_all(self, include_browser: bool = True) -> dict:
        """
        Запустить все парсеры и собрать события.
        
        Args:
            include_browser: Включать ли browser-парсеры (медленнее, но больше источников)
        
        Returns:
            Статистика парсинга
        """
        total_parsed = 0
        total_saved = 0
        errors = []
        
        # 1. HTTP-парсеры (быстрые)
        print("\n── HTTP-парсеры ──")
        for parser in self.http_parsers:
            stats = await self._run_parser(parser)
            total_parsed += stats["parsed"]
            total_saved += stats["saved"]
            if stats["error"]:
                errors.append(stats["error"])
        
        # 2. Browser-парсеры (медленные)
        if include_browser:
            print("\n── Browser-парсеры (Playwright) ──")
            for parser in self.browser_parsers:
                stats = await self._run_parser(parser)
                total_parsed += stats["parsed"]
                total_saved += stats["saved"]
                if stats["error"]:
                    errors.append(stats["error"])
        
        return {
            "total_parsed": total_parsed,
            "total_saved": total_saved,
            "errors": errors,
        }
    
    async def parse_http_only(self) -> dict:
        """Запустить только HTTP-парсеры (быстро, без браузера)."""
        return await self.parse_all(include_browser=False)
    
    async def _run_parser(self, parser) -> dict:
        """Запустить один парсер."""
        result = {"parsed": 0, "saved": 0, "error": None}
        
        try:
            print(f"[...] {parser.source_name}...")
            
            async with parser:
                events = await parser.parse()
                
                if events:
                    saved = await self._save_events(events)
                    result["parsed"] = len(events)
                    result["saved"] = saved
                    print(f"[OK]  {parser.source_name}: found {len(events)}, saved {saved} new")
                else:
                    print(f"[---] {parser.source_name}: no events found")
        
        except Exception as e:
            error_msg = f"{parser.source_name}: {type(e).__name__}: {str(e)[:100]}"
            result["error"] = error_msg
            print(f"[ERR] {error_msg}")
        
        return result
    
    async def _save_events(self, events: List[EventData]) -> int:
        """
        Сохранить события в базу данных.
        Фильтрует прошедшие события (date_start < сейчас).
        
        Returns:
            Количество сохраненных событий
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        saved_count = 0
        
        for event_data in events:
            try:
                # Пропускаем прошедшие события
                if event_data.date_start < now:
                    continue
                
                existing = await self._check_duplicate(event_data.source_url)
                
                if not existing:
                    event_dict = event_data.to_dict()
                    event_dict = self._validate_event_data(event_dict)
                    
                    from src.database.models.event import Event
                    event = Event(**event_dict)
                    self.session.add(event)
                    saved_count += 1
            
            except Exception as e:
                print(f"  Error saving event '{event_data.title[:50]}': {e}")
                continue
        
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            print(f"  Error committing events: {e}")
            return 0
        
        return saved_count
    
    def _validate_event_data(self, event_dict: dict) -> dict:
        """Валидировать и обрезать длинные поля события."""
        max_lengths = {
            'title': 500,
            'location': 500,
            'address': 1000,
            'source_url': 1000,
            'image_url': 1000,
        }
        
        for field, max_length in max_lengths.items():
            if field in event_dict and event_dict[field]:
                value = str(event_dict[field])
                if len(value) > max_length:
                    event_dict[field] = value[:max_length - 3] + '...'
        
        if not event_dict.get('title') or len(event_dict['title'].strip()) == 0:
            event_dict['title'] = 'Без названия'
        
        return event_dict
    
    async def _check_duplicate(self, source_url: str) -> bool:
        """Проверить существует ли событие с таким URL."""
        from sqlalchemy import select
        from src.database.models.event import Event
        
        result = await self.session.execute(
            select(Event).where(Event.source_url == source_url)
        )
        
        return result.scalar_one_or_none() is not None
