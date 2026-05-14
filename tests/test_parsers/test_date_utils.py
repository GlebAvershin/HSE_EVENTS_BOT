"""Тесты утилит парсинга дат на русском языке."""
import pytest
from datetime import datetime, timedelta

from src.parsers.date_utils import parse_russian_date, _guess_year


class TestParseRussianDate:
    """Тесты для parse_russian_date."""

    def test_parse_russian_date_full(self):
        """Тест парсинга полной даты: '15 апреля 2026'."""
        result = parse_russian_date("15 апреля 2026")

        assert result is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 15

    def test_parse_russian_date_no_year(self):
        """Тест парсинга даты без года: '15 мая' — текущий или следующий год."""
        result = parse_russian_date("15 мая")

        assert result is not None
        assert result.month == 5
        assert result.day == 15
        # Год определяется автоматически
        assert result.year in (datetime.now().year, datetime.now().year + 1)

    def test_parse_russian_date_past_month(self):
        """Тест парсинга даты с прошедшим месяцем: '15 января' — следующий год если прошло >60 дней."""
        now = datetime.now()
        # Если январь прошёл более 60 дней назад, должен быть следующий год
        result = parse_russian_date("15 января")

        assert result is not None
        assert result.month == 1
        assert result.day == 15

        # Проверяем логику: если сейчас после марта, то январь = следующий год
        jan_15 = datetime(now.year, 1, 15)
        if jan_15 < now - timedelta(days=60):
            assert result.year == now.year + 1
        else:
            assert result.year == now.year

    def test_parse_russian_date_iso(self):
        """Тест парсинга ISO формата: '2026-05-15'."""
        result = parse_russian_date("2026-05-15")

        assert result is not None
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0

    def test_parse_russian_date_dot_format(self):
        """Тест парсинга формата с точками: '15.05.2026'."""
        result = parse_russian_date("15.05.2026")

        assert result is not None
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 15

    def test_parse_russian_date_with_time(self):
        """Тест парсинга даты с временем: '15 мая 19:00'."""
        result = parse_russian_date("15 мая 19:00")

        assert result is not None
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 19
        assert result.minute == 0

    def test_parse_russian_date_today(self):
        """Тест парсинга 'сегодня'."""
        result = parse_russian_date("сегодня")

        assert result is not None
        now = datetime.now()
        assert result.year == now.year
        assert result.month == now.month
        assert result.day == now.day

    def test_parse_russian_date_tomorrow(self):
        """Тест парсинга 'завтра'."""
        result = parse_russian_date("завтра")

        assert result is not None
        tomorrow = datetime.now() + timedelta(days=1)
        assert result.year == tomorrow.year
        assert result.month == tomorrow.month
        assert result.day == tomorrow.day

    def test_parse_russian_date_invalid(self):
        """Тест парсинга невалидной строки — возвращает None."""
        result = parse_russian_date("это не дата вообще")
        assert result is None

        result = parse_russian_date("")
        assert result is None

        result = parse_russian_date("   ")
        assert result is None


class TestGuessYear:
    """Тесты для _guess_year."""

    def test_guess_year_recent_past(self):
        """Тест: дата в пределах 60 дней назад = текущий год."""
        now = datetime.now()
        # Берём месяц, который точно в пределах 60 дней
        recent_date = now - timedelta(days=30)
        year = _guess_year(recent_date.month, recent_date.day)
        assert year == now.year

    def test_guess_year_far_past(self):
        """Тест: дата более 60 дней назад = следующий год."""
        now = datetime.now()
        # Берём дату, которая точно прошла более 60 дней назад
        far_past = now - timedelta(days=90)
        year = _guess_year(far_past.month, far_past.day)
        assert year == now.year + 1

    def test_guess_year_future(self):
        """Тест: будущая дата = текущий год."""
        now = datetime.now()
        future_date = now + timedelta(days=60)
        year = _guess_year(future_date.month, future_date.day)
        assert year == now.year
