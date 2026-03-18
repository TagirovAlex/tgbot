"""
Фильтры для проверки прав доступа.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

import config
from database.repositories.users import User


class IsAdminFilter(BaseFilter):
    """
    Фильтр для проверки прав администратора.
    
    Проверяет как конфигурационный список ADMIN_IDS,
    так и флаг is_admin в базе данных.
    """
    
    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User = None
    ) -> bool:
        tg_user = event.from_user
        
        # Проверяем конфиг
        if tg_user.id in config.ADMIN_IDS:
            return True
        
        # Проверяем БД
        if user and user.is_admin:
            return True
        
        return False


class IsOwnerFilter(BaseFilter):
    """Фильтр для проверки владельца ресурса."""
    
    def __init__(self, owner_field: str = "user_id"):
        self.owner_field = owner_field
    
    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User = None,
        **kwargs
    ) -> bool:
        if not user:
            return False
        
        # Проверяем что ресурс принадлежит пользователю
        resource = kwargs.get("resource")
        if resource and hasattr(resource, self.owner_field):
            return getattr(resource, self.owner_field) == user.id
        
        return True