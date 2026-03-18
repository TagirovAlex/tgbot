"""
Фильтры для проверки прав доступа.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, TelegramObject

import config


class IsAdminFilter(BaseFilter):
    """
    Фильтр для проверки прав администратора.
    
    Проверяет как конфигурационный список ADMIN_IDS,
    так и флаг is_admin в базе данных.
    """
    
    async def __call__(
        self,
        event: TelegramObject,
        user=None,
        **kwargs
    ) -> bool:
        # Получаем telegram user
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        
        if not tg_user:
            return False
        
        # Проверяем конфиг
        if tg_user.id in config.ADMIN_IDS:
            return True
        
        # Проверяем БД
        if user and hasattr(user, 'is_admin') and user.is_admin:
            return True
        
        return False


class IsOwnerFilter(BaseFilter):
    """
    Фильтр для проверки владельца ресурса.
    
    Проверяет, что ресурс принадлежит текущему пользователю.
    Администраторы имеют доступ ко всем ресурсам.
    
    Args:
        owner_field: Название поля с ID владельца (по умолчанию 'user_id')
        allow_admin: Разрешить доступ администраторам (по умолчанию True)
    
    Example:
        @router.callback_query(F.data.startswith("note_edit:"), IsOwnerFilter())
        async def edit_note(callback: CallbackQuery, user: User):
            ...
    """
    
    def __init__(self, owner_field: str = "user_id", allow_admin: bool = True):
        self.owner_field = owner_field
        self.allow_admin = allow_admin
    
    async def __call__(
        self,
        event: TelegramObject,
        user=None,
        resource=None,
        **kwargs
    ) -> bool:
        if not user:
            return False
        
        # Администраторы имеют доступ ко всему
        if self.allow_admin:
            if hasattr(user, 'is_admin') and user.is_admin:
                return True
            
            # Проверяем конфиг
            tg_user = None
            if isinstance(event, Message):
                tg_user = event.from_user
            elif isinstance(event, CallbackQuery):
                tg_user = event.from_user
            
            if tg_user and tg_user.id in config.ADMIN_IDS:
                return True
        
        # Проверяем владельца ресурса
        if resource and hasattr(resource, self.owner_field):
            owner_id = getattr(resource, self.owner_field)
            return owner_id == user.id
        
        # Если ресурс не передан, пропускаем (проверка будет в обработчике)
        return True