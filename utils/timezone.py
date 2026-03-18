"""
Утилиты для работы с часовыми поясами.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
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


def ensure_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Преобразование значения в datetime.
    
    SQLite возвращает datetime как строку, эта функция
    конвертирует строку обратно в datetime.
    
    Args:
        value: Строка, datetime или None
        
    Returns:
        datetime объект или None
    """
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        # Пробуем разные форматы SQLite
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        # Если ничего не подошло, возвращаем None
        return None
    
    return None


def user_time_to_utc(
    local_time: Union[str, datetime],
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
    # Преобразуем в datetime если это строка
    local_time = ensure_datetime(local_time)
    if local_time is None:
        return datetime.utcnow()
    
    tz = get_user_timezone(user_timezone)
    
    # Если время "наивное" (без timezone info), локализуем его
    if local_time.tzinfo is None:
        local_time = tz.localize(local_time)
    
    return local_time.astimezone(pytz.UTC).replace(tzinfo=None)


def utc_to_user_time(
    utc_time: Union[str, datetime],
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
    # Преобразуем в datetime если это строка
    utc_time = ensure_datetime(utc_time)
    if utc_time is None:
        return datetime.now()
    
    tz = get_user_timezone(user_timezone)
    
    # Добавляем UTC timezone info если его нет
    if utc_time.tzinfo is None:
        utc_time = pytz.UTC.localize(utc_time)
    
    return utc_time.astimezone(tz)


def format_user_time(
    utc_time: Union[str, datetime, None],
    user_timezone: str,
    format_str: str = "%d.%m.%Y %H:%M"
) -> str:
    """
    Форматирование времени для отображения пользователю.
    
    Args:
        utc_time: Время в UTC (строка или datetime)
        user_timezone: Часовой пояс пользователя
        format_str: Формат вывода
        
    Returns:
        Отформатированная строка времени
    """
    # Преобразуем в datetime если это строка
    utc_time = ensure_datetime(utc_time)
    
    if utc_time is None:
        return "—"
    
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


def format_datetime_short(
    dt: Union[str, datetime, None],
    user_timezone: str = "UTC"
) -> str:
    """
    Короткое форматирование даты/времени.
    
    Args:
        dt: datetime или строка
        user_timezone: Часовой пояс пользователя
        
    Returns:
        Отформатированная строка
    """
    return format_user_time(dt, user_timezone, "%d.%m %H:%M")