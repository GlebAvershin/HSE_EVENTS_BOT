FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry

# Копирование файлов зависимостей
COPY pyproject.toml ./

# Установка зависимостей
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копирование кода приложения
COPY src ./src

# Запуск API
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
