"""
Утилиты для работы с часовыми поясами.
"""

from datetime import datetime, timedelta
from typing import Optional
import pytz

import config


# Популярные часовые пояса для выбора
POPULAR_TIMEZONES = [
    ("UTC", "UTC (±00:00)"),
    ("Europe/Moscow", "Москва (UTC+03:00)"),
    ("Europe/Kiev", "Киев (UTC+02:00)"),
    ("Europe/Minsk", "Минск (UTC+03:00)"),
    ("Asia/Almaty", "Алматы (UTC+06:00)"),
    ("Asia/Tashkent", "Ташкент (UTC+05:00)"),
    ("Asia/Yekaterinburg", "Екатеринбург (UTC+05:00)"),
    ("Asia/Novosibirsk", "Новосибирск (UTC+07:00)"),
    ("Asia/Vladivostok", "Владивосток (UTC+10:00)"),
    ("Europe/London", "Лондон (UTC±00:00)"),
    ("Europe/Berlin", "Берлин (UTC+01:00)"),
    ("America/New_York", "Нью-Йорк (UTC-05:00)"),
    ("America/Los_Angeles", "Лос-Анджелес (UTC-08:00)"),
]


def get_server_timezone() -> pytz.timezone:
    """Получение часового пояса сервера."""
    return pytz.timezone(config.SERVER_TIMEZONE)


def get_user_timezone(timezone_str: str) -> pytz.timezone:
    """
    Получение объекта часового пояса по строке.
    
    Args:
        timezone_str: Название часового пояса (например, 'Europe/Moscow')
        
    Returns:
        Объект pytz.timezone
    """
    try:
        return pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        return pytz.UTC


def user_time_to_utc(
    local_time: datetime,
    user_timezone: str
) -> datetime:
    """
    Конвертация времени пользователя в UTC.
    
    Args:
        local_time: Время в часовом поясе пользователя
        user_timezone: Часовой пояс пользователя
        
    Returns:
        Время в UTC
    """
    tz = get_user_timezone(user_timezone)
    
    # Если время "наивное" (без timezone info), локализуем его
    if local_time.tzinfo is None:
        local_time = tz.localize(local_time)
    
    return local_time.astimezone(pytz.UTC).replace(tzinfo=None)


def utc_to_user_time(
    utc_time: datetime,
    user_timezone: str
) -> datetime:
    """
    Конвертация времени UTC в время пользователя.
    
    Args:
        utc_time: Время в UTC
        user_timezone: Часовой пояс пользователя
        
    Returns:
        Время в часовом поясе пользователя
    """
    tz = get_user_timezone(user_timezone)
    
    # Добавляем UTC timezone info если его нет
    if utc_time.tzinfo is None:
        utc_time = pytz.UTC.localize(utc_time)
    
    return utc_time.astimezone(tz)


def format_user_time(
    utc_time: datetime,
    user_timezone: str,
    format_str: str = "%d.%m.%Y %H:%M"
) -> str:
    """
    Форматирование времени для отображения пользователю.
    
    Args:
        utc_time: Время в UTC
        user_timezone: Часовой пояс пользователя
        format_str: Формат вывода
        
    Returns:
        Отформатированная строка времени
    """
    local_time = utc_to_user_time(utc_time, user_timezone)
    return local_time.strftime(format_str)


def parse_user_datetime(
    datetime_str: str,
    user_timezone: str,
    formats: Optional[list[str]] = None
) -> Optional[datetime]:
    """
    Парсинг строки даты/времени от пользователя.
    
    Args:
        datetime_str: Строка с датой и временем
        user_timezone: Часовой пояс пользователя
        formats: Список форматов для парсинга
        
    Returns:
        datetime в UTC или None если не удалось распарсить
    """
    if formats is None:
        formats = [
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M",
        ]
    
    for fmt in formats:
        try:
            local_time = datetime.strptime(datetime_str.strip(), fmt)
            return user_time_to_utc(local_time, user_timezone)
        except ValueError:
            continue
    
    return None


def get_timezone_offset(timezone_str: str) -> str:
    """Получение смещения часового пояса в формате ±HH:MM."""
    tz = get_user_timezone(timezone_str)
    now = datetime.now(tz)
    offset = now.strftime('%z')
    return f"{offset[:3]}:{offset[3:]}"