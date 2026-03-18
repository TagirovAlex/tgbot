"""
Middleware для логирования действий пользователей.
"""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database.database import Database

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования всех действий пользователей.
    
    Записывает в базу данных и в файл логов информацию о каждом
    входящем сообщении и callback-запросе.
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Определяем пользователя и действие
        user = None
        action = ""
        details = ""
        
        if isinstance(event, Message):
            user = event.from_user
            action = "message"
            if event.text:
                details = event.text[:200]
            elif event.document:
                action = "document"
                details = event.document.file_name
            elif event.photo:
                action = "photo"
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            action = "callback"
            details = event.data
        
        # Логируем
        if user:
            logger.info(
                f"User {user.id} (@{user.username}): {action} - {details[:50]}"
            )
            
            # Сохраняем в БД (получаем user_id из data если есть)
            db_user = data.get("user")
            if db_user:
                await self._log_to_db(db_user.id, action, details)
        
        # Продолжаем обработку
        return await handler(event, data)
    
    async def _log_to_db(self, user_id: int, action: str, details: str):
        """Запись лога в базу данных."""
        try:
            await self.db.execute(
                """
                INSERT INTO action_logs (user_id, action, details)
                VALUES (?, ?, ?)
                """,
                (user_id, action, details[:500])
            )
        except Exception as e:
            logger.error(f"Ошибка записи лога: {e}")