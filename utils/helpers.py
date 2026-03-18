"""
Вспомогательные функции.
"""

from typing import Optional
import re


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезка текста до указанной длины.
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """Экранирование HTML символов."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def parse_interval(interval_str: str) -> Optional[int]:
    """
    Парсинг строки интервала в минуты.
    
    Поддерживаемые форматы:
    - "30m", "30м" - минуты
    - "2h", "2ч" - часы
    - "1d", "1д" - дни
    - "1w", "1н" - недели
    
    Args:
        interval_str: Строка интервала
        
    Returns:
        Количество минут или None
    """
    interval_str = interval_str.strip().lower()
    
    patterns = [
        (r'^(\d+)\s*[mм]$', 1),        # минуты
        (r'^(\d+)\s*[hч]$', 60),       # часы
        (r'^(\d+)\s*[dд]$', 1440),     # дни
        (r'^(\d+)\s*[wн]$', 10080),    # недели
    ]
    
    for pattern, multiplier in patterns:
        match = re.match(pattern, interval_str)
        if match:
            return int(match.group(1)) * multiplier
    
    # Попробуем просто число (минуты)
    try:
        return int(interval_str)
    except ValueError:
        return None


def format_interval(minutes: int) -> str:
    """
    Форматирование интервала в читаемый вид.
    
    Args:
        minutes: Количество минут
        
    Returns:
        Читаемая строка интервала
    """
    if minutes == 0:
        return "Одноразово"
    
    if minutes < 60:
        return f"{minutes} мин."
    
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ч."
    
    days = hours // 24
    if days < 7:
        return f"{days} д."
    
    weeks = days // 7
    return f"{weeks} нед."