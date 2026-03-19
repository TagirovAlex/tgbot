"""
Модуль для работы с базой данных SQLite в асинхронном режиме.
"""

import aiosqlite
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Асинхронный менеджер базы данных SQLite.
    
    Attributes:
        db_path: Путь к файлу базы данных
        connection: Активное соединение с базой данных
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def init(self):
        """Инициализация базы данных и создание таблиц."""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        
        await self._create_tables()
        logger.info(f"База данных инициализирована: {self.db_path}")
    
    async def _create_tables(self):
        """Создание таблиц базы данных."""
        await self.connection.executescript("""
            -- Пользователи
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                timezone TEXT DEFAULT 'UTC',
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Заметки
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Напоминания
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                remind_at TIMESTAMP NOT NULL,
                repeat_interval INTEGER DEFAULT 0,
                is_group INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                last_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Шаблоны
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('note', 'reminder')),
                title_template TEXT,
                content_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            -- Логи действий
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            
            -- Полученные файлы
            CREATE TABLE IF NOT EXISTS received_files (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_name TEXT,
                file_path TEXT NOT NULL,
                file_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            -- Настройки бота
            CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
            -- Настройки бота
            CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
            -- Индексы
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);
            CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
            CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
            CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active);
            CREATE INDEX IF NOT EXISTS idx_templates_user_id ON templates(user_id);
            CREATE INDEX IF NOT EXISTS idx_action_logs_user_id ON action_logs(user_id);
            
        """)
        await self.connection.commit()
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Выполнение SQL-запроса."""
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        return cursor
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        """Получение одной записи."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
        """Получение всех записей."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchall()
    
    async def close(self):
        """Закрытие соединения с базой данных."""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с базой данных закрыто")