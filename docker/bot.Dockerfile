FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей (включая для Playwright/Chromium)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    # Зависимости Playwright/Chromium
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Установка Chromium для Playwright
RUN python -m playwright install chromium

# Копирование кода приложения
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Запуск бота
CMD ["python", "-m", "src.bot.main"]
