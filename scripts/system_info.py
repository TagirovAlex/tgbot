#!/usr/bin/env python3
"""
Скрипт для получения информации о системе.
Доступен для выполнения через админ-панель бота.
"""

import platform
import sys
import os
from datetime import datetime


def main():
    print("=" * 50)
    print("СИСТЕМНАЯ ИНФОРМАЦИЯ")
    print("=" * 50)
    print()
    
    print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python версия: {sys.version}")
    print(f"Платформа: {platform.platform()}")
    print(f"Архитектура: {platform.machine()}")
    print(f"Процессор: {platform.processor()}")
    print()
    
    print("Переменные окружения:")
    for key in ["PATH", "HOME", "USER", "LANG"]:
        value = os.environ.get(key, "не установлено")
        print(f"  {key}: {value[:50]}...")
    
    print()
    print("=" * 50)
    print("Скрипт выполнен успешно!")
    print("=" * 50)


if __name__ == "__main__":
    main()