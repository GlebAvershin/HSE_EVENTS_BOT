"""Healthcheck скрипт для Docker.

Проверяет что бот жив по файлу-маркеру heartbeat.
Бот обновляет /tmp/bot_heartbeat каждые 30 секунд.
Если файл старше 120 секунд — бот считается мёртвым.
"""
import os
import sys
import time

HEARTBEAT_FILE = "/tmp/bot_heartbeat"
MAX_AGE_SECONDS = 90  # Если heartbeat старше 90 секунд — unhealthy


def check():
    """Проверить состояние бота по heartbeat файлу."""
    if not os.path.exists(HEARTBEAT_FILE):
        print("UNHEALTHY: No heartbeat file")
        sys.exit(1)

    mtime = os.path.getmtime(HEARTBEAT_FILE)
    age = time.time() - mtime

    if age > MAX_AGE_SECONDS:
        print(f"UNHEALTHY: Heartbeat is {int(age)}s old (max {MAX_AGE_SECONDS}s)")
        sys.exit(1)

    print(f"HEALTHY: Heartbeat {int(age)}s ago")
    sys.exit(0)


if __name__ == "__main__":
    check()
