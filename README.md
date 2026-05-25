<h1 align="center">
  <br>
  🤖 NN Events Bot
  <br>
</h1>

<p align="center">
  <b>Платформа для автоматической агрегации IT и развлекательных мероприятий Нижнего Новгорода</b><br>
  Telegram-бот · Веб-админка · Автопарсинг 11 источников
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/aiogram-3.x-blue?logo=telegram&logoColor=white" alt="aiogram">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <a href="https://t.me/NN_HSE_Events_Bot">🚀 Открыть бота</a> ·
  <a href="#быстрый-старт">Установка</a> ·
  <a href="#архитектура">Архитектура</a> ·
  <a href="#источники-данных">Источники</a>
</p>

---

## 📋 О проекте

**NN Events Bot** — платформа, которая автоматически собирает информацию о городских мероприятиях из 11 источников и предоставляет единый интерфейс для поиска событий и совместного планирования посещений через систему социальных связей.

### Ключевые возможности

| Модуль | Описание |
|--------|----------|
| 🔍 **Агрегация** | Автоматический парсинг 11 источников каждые 12 часов |
| 📱 **Telegram-бот** | Просмотр, поиск, фильтры, календарь, пагинация |
| 👥 **Социальная система** | Друзья, совместное планирование, уведомления |
| 🛡️ **Админ-панель** | Веб-интерфейс для модерации событий и управления источниками |
| 📊 **Аналитика** | Дашборд со статистикой, метриками и состоянием парсеров |

---

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose
- Git

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/GlebAvershin/HSE_EVENTS_BOT.git
cd HSE_EVENTS_BOT

# 2. Создать .env файл
cp .env.example .env
# Заполнить BOT_TOKEN и API_SECRET_KEY в .env

# 3. Запустить все сервисы
docker compose up -d

# 4. Создать администратора для веб-панели
docker compose exec bot python -m scripts.create_admin admin admin123456
```

### Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| Telegram-бот | [@NN_HSE_Events_Bot](https://t.me/NN_HSE_Events_Bot) | Основной интерфейс |
| Админ-панель | `http://localhost:3000` | Модерация и управление |
| REST API | `http://localhost:8000` | FastAPI + Swagger docs |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                           │
├──────────────┬──────────────┬───────────┬──────┬───────────┤
│  Telegram    │   FastAPI    │   React   │      │           │
│    Bot       │    API       │   Admin   │Redis │ PostgreSQL│
│  (aiogram)   │  (uvicorn)   │  (nginx)  │      │    15     │
├──────────────┴──────────────┴───────────┤      │           │
│         Python 3.11 + Playwright        │      │           │
│    Парсеры · Сервисы · Репозитории      │      │           │
└─────────────────────────────────────────┴──────┴───────────┘
```

### Технологический стек

| Слой | Технологии |
|------|-----------|
| **Бот** | Python 3.11, aiogram 3.x, APScheduler |
| **Парсинг** | aiohttp, BeautifulSoup4, Playwright (Chromium) |
| **API** | FastAPI, Pydantic, JWT (bcrypt + PyJWT) |
| **Фронтенд** | React 18, TypeScript, TailwindCSS, React Query |
| **БД** | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| **Кеш/FSM** | Redis 7 |
| **Инфраструктура** | Docker Compose, Nginx, Poetry |

---

## 📡 Источники данных

Парсеры запускаются автоматически каждые 12 часов. Прошедшие события удаляются ежедневно в 03:00.

| Источник | Метод | Категория | Событий/цикл |
|----------|-------|-----------|:------------:|
| IT52.info | HTTP / Atom | IT | ~20 |
| Habr Events | HTTP / HTML | IT | ~4 |
| Networkly | HTTP / HTML | IT | ~5 |
| All-Events | HTTP / HTML | IT | ~3 |
| Gorodzovet | HTTP / HTML | IT | ~3 |
| Top Academy | HTTP / HTML | IT | ~7 |
| Timepad | Browser (Playwright) | IT | ~3 |
| KudaGo | REST API | Развлечения | ~8 |
| Milo Concert Hall | HTTP / HTML | Развлечения | ~16 |
| Kassir.ru | Browser (Playwright) | Развлечения | ~30 |
| QTickets | Browser (Playwright) | Развлечения | ~18 |

**Итого:** ~100+ событий за цикл парсинга

---

## 📱 Функции Telegram-бота

### Команды

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация и главное меню |
| `/events` | Все события с фильтрами |
| `/calendar` | Календарь (сегодня/неделя/месяц) |
| `/friends` | Управление друзьями |
| `/profile` | Профиль и настройки |
| `/help` | Справка |

### Социальные функции

- **Система дружбы** — добавление по username и реферальной ссылке
- **Совместное планирование** — отметки "Я пойду" / "Возможно", видно кто из друзей идёт
- **Уведомления** — о планах друзей, напоминания за 24ч и 1ч до события
- **Приватность** — скрытие посещений, скрытие из поиска
- **Рейтинги** — оценки 1–5 звёзд и комментарии к событиям

---

## 🛡️ Админ-панель

Веб-интерфейс для управления платформой:

- **Dashboard** — статистика событий, пользователей, состояние парсеров
- **События** — CRUD, фильтры по статусу/категории, поиск, публикация
- **Источники** — управление парсерами, toggle активности

**Аутентификация:** JWT (access 30 мин + refresh 7 дней), bcrypt, rate limiter

---

## 🗄️ База данных

```
users                    events                  friendships
├── telegram_id          ├── title               ├── user_id
├── username             ├── description         ├── friend_id
├── first_name           ├── category            └── status
├── referral_code        ├── date_start
└── referred_by          ├── location            event_attendances
                         ├── source_url          ├── user_id
user_settings            ├── is_published        ├── event_id
├── notify_new_events    └── image_url           └── status (going/maybe)
├── notify_friend_going
├── hide_attendance      admin_users             notifications
└── hide_from_search     ├── username            ├── user_id
                         └── password_hash       ├── type
event_sources                                    └── message
├── name                 event_reviews
├── parser_type          ├── user_id             event_comments
├── is_active            ├── event_id            ├── user_id
└── last_parsed_at       └── rating (1-5)        └── text
```

---

## 🧪 Тестирование

| Уровень | Кол-во | Охват |
|---------|:------:|-------|
| Import-тесты | 6 | Корректность импортов модулей |
| Unit: date_utils | 8 | ISO 8601, текстовые форматы, edge cases |
| Unit: event_service | 10 | CRUD, фильтрация, дедупликация |
| Unit: config | 4 | Переменные окружения, типизация |
| Integration API | 20 | auth, events CRUD, stats (httpx + ASGI) |
| Ручные E2E | 7 | Полные сценарии в Telegram и веб-панели |

```bash
# Запуск тестов
docker compose exec bot pytest tests/ -v
```

---

## 📁 Структура проекта

```
├── src/
│   ├── bot/                    # Telegram-бот (aiogram)
│   │   ├── handlers/           # Обработчики команд
│   │   ├── keyboards/          # Клавиатуры и кнопки
│   │   └── main.py             # Точка входа + scheduler
│   ├── api/                    # FastAPI админ-панель
│   │   └── admin/              # auth, events, sources, stats
│   ├── parsers/                # 11 парсеров событий
│   ├── services/               # Бизнес-логика
│   ├── database/               # Модели, репозитории, миграции
│   └── config.py               # Конфигурация из .env
├── admin-panel/                # React + TypeScript + Tailwind
├── alembic/                    # Миграции БД
├── docker/                     # Dockerfiles
├── tests/                      # Тесты
├── scripts/                    # Утилиты (create_admin, healthcheck)
└── docker-compose.yml          # Оркестрация 5 контейнеров
```

---

## 📈 Метрики качества

По ГОСТ Р ИСО/МЭК 25010–2015:

| Метрика | Значение |
|---------|----------|
| Функциональная полнота | 1,00 — все функции из ТЗ реализованы |
| Надёжность | 99,6% (498/500 операций) |
| Полнота парсинга | 94,9% (203 из 214 событий) |
| Доставка уведомлений | 98,9% (346 из 350 сообщений) |
| Время ответа бота | Среднее 30 мс |
| Тесты | 50 тестов, 0 упавших |

---

## 👥 Авторы

- **Глеб Авершин, Дмитрий Егоров** 

**Курсовая работа** · НИУ ВШЭ Нижний Новгород · Компьютерные науки и технологии · 2026

---

## 📄 Лицензия

Учебный проект. Все права защищены.
