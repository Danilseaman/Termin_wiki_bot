from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    telegram_id: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    is_registered: bool = False
    registration_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    search_count: int = 0

    def __post_init__(self):
        """Парсинг дат после инициализации"""
        self.registration_date = self._parse_datetime(self.registration_date)
        self.last_activity = self._parse_datetime(self.last_activity)

    def _parse_datetime(self, date_value):
        """Парсинг даты из разных форматов"""
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                # Пробуем разные форматы
                formats = [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with T
                    "%Y-%m-%dT%H:%M:%S",  # ISO format without microseconds
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass

        return None


@dataclass
class SearchHistory:
    """Модель истории поиска"""
    id: Optional[int] = None
    user_id: int = 0
    search_term: str = ""
    result_title: Optional[str] = None
    result_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    success: bool = True

    def __post_init__(self):
        """Парсинг дат после инициализации"""
        self.timestamp = self._parse_datetime(self.timestamp)

    def _parse_datetime(self, date_value):
        """Парсинг даты из разных форматов"""
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                formats = [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with T
                    "%Y-%m-%dT%H:%M:%S",  # ISO format without microseconds
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass

        return None


@dataclass
class BotStats:
    """Модель статистики бота"""
    total_users: int = 0
    active_users: int = 0
    total_searches: int = 0
    successful_searches: int = 0
    popular_terms: list = None

    def __post_init__(self):
        if self.popular_terms is None:
            self.popular_terms = []