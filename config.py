"""
Конфигурация приложения.
Загружает настройки из переменных окружения.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

# Администраторы (список Telegram ID)
ADMIN_IDS: list[int] = [
    int(admin_id.strip()) 
    for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
    if admin_id.strip()
]

# База данных
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database.db")

# Директории
SCRIPTS_DIR = BASE_DIR / os.getenv("SCRIPTS_DIR", "scripts")
FILES_DIR = BASE_DIR / os.getenv("FILES_DIR", "storage/files")
LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "logs")

# Создание директорий если не существуют
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Часовой пояс сервера
SERVER_TIMEZONE = os.getenv("SERVER_TIMEZONE", "UTC")

# Интервалы повтора напоминаний (в минутах)
REMINDER_INTERVALS = {
    "once": 0,
    "hourly": 60,
    "daily": 1440,
    "weekly": 10080,
    "monthly": 43200,
}