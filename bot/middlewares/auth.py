"""
Middleware для аутентификации и авторизации пользователей.
"""

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

import config
from database.database import Database
from database.repositories import UserRepository


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для автоматической регистрации и загрузки данных пользователя.
    
    - Автоматически создаёт пользователя в БД при первом обращении
    - Загружает данные пользователя в контекст data["user"]
    - Устанавливает флаг is_admin для администраторов из config
    """
    
    def __init__(self, db: Database):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем Telegram пользователя
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        
        if tg_user:
            # Получаем или создаём пользователя в БД
            user = await self.user_repo.get_or_create(
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name
            )
            
            # Проверяем, является ли пользователь админом из конфига
            if tg_user.id in config.ADMIN_IDS and not user.is_admin:
                await self.user_repo.set_admin(user.id, True)
                user = await self.user_repo.get_by_id(user.id)
            
            # Добавляем в контекст
            data["user"] = user
            data["db"] = self.db
        
        return await handler(event, data)