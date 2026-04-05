"""Скрипт для добавления тестовых событий в БД."""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database.repositories.event import EventRepository


async def add_test_events():
    """Добавить тестовые события."""
    # Создаем движок и сессию
    engine = create_async_engine(settings.database_url, echo=True)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        event_repo = EventRepository(session)

        # Текущая дата
        now = datetime.utcnow()

        # IT-мероприятия
        it_events = [
            {
                "title": "Python Meetup Нижний Новгород",
                "category": "it",
                "date_start": now + timedelta(days=3, hours=18),
                "description": "Встреча Python-разработчиков. Обсудим новые фичи Python 3.12, "
                "поделимся опытом и пообщаемся за чашкой кофе.",
                "location": "IT-Park",
                "address": "ул. Родионова, 165",
                "source_url": "https://example.com/python-meetup",
                "is_published": True,
            },
            {
                "title": "Хакатон: AI для бизнеса",
                "category": "it",
                "date_start": now + timedelta(days=7, hours=10),
                "date_end": now + timedelta(days=8, hours=18),
                "description": "48-часовой хакатон по разработке AI-решений для бизнеса. "
                "Призовой фонд 500 000 рублей!",
                "location": "Точка кипения",
                "address": "Большая Покровская, 60",
                "source_url": "https://example.com/ai-hackathon",
                "is_published": True,
            },
            {
                "title": "Конференция DevOps Days",
                "category": "it",
                "date_start": now + timedelta(days=14, hours=9),
                "description": "Двухдневная конференция о DevOps практиках, CI/CD, "
                "контейнеризации и облачных технологиях.",
                "location": "Конгресс-центр",
                "address": "пл. Минина и Пожарского, 2",
                "source_url": "https://example.com/devops-days",
                "is_published": True,
            },
        ]

        # Развлекательные мероприятия
        entertainment_events = [
            {
                "title": "Концерт: Би-2",
                "category": "entertainment",
                "date_start": now + timedelta(days=5, hours=20),
                "description": "Легендарная группа Би-2 с новой программой. "
                "Исполнят все хиты и новые песни.",
                "location": "ДК ГАЗ",
                "address": "пр. Ленина, 12",
                "source_url": "https://example.com/bi2-concert",
                "is_published": True,
            },
            {
                "title": "Stand-up: Слава Комиссаренко",
                "category": "entertainment",
                "date_start": now + timedelta(days=10, hours=19),
                "description": "Сольный концерт популярного стендап-комика. "
                "Новая программа 'Всё сложно'.",
                "location": "Театр драмы",
                "address": "ул. Большая Покровская, 13",
                "source_url": "https://example.com/standup",
                "is_published": True,
            },
            {
                "title": "Фестиваль уличной еды",
                "category": "entertainment",
                "date_start": now + timedelta(days=2, hours=12),
                "date_end": now + timedelta(days=2, hours=22),
                "description": "Более 50 фудтраков с кухнями со всего мира. "
                "Живая музыка, мастер-классы и развлечения.",
                "location": "Парк Швейцария",
                "address": "ул. Белинского, 34",
                "source_url": "https://example.com/food-fest",
                "is_published": True,
            },
        ]

        # Добавляем IT-события
        print("\n🔵 Добавление IT-мероприятий...")
        for event_data in it_events:
            event = await event_repo.create(**event_data)
            print(f"✅ Добавлено: {event.title}")

        # Добавляем развлекательные события
        print("\n🎉 Добавление развлекательных мероприятий...")
        for event_data in entertainment_events:
            event = await event_repo.create(**event_data)
            print(f"✅ Добавлено: {event.title}")

    await engine.dispose()
    print("\n✨ Все тестовые события успешно добавлены!")


if __name__ == "__main__":
    print("🚀 Запуск скрипта добавления тестовых событий...\n")
    asyncio.run(add_test_events())
