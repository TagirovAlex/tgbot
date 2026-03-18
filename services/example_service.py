"""
Пример создания пользовательского сервиса.

Этот модуль демонстрирует, как создавать собственные сервисы для расширения
функциональности бота. Сервисы инкапсулируют бизнес-логику и предоставляют
чистый API для обработчиков.

Example:
    >>> from services.example_service import ExampleService
    >>> 
    >>> # В обработчике
    >>> async def my_handler(message: Message, db: Database):
    ...     service = ExampleService(db)
    ...     result = await service.process_data(message.text)
    ...     await message.reply(result)

Note:
    При создании своего сервиса:
    1. Наследуйтесь от BaseService
    2. Определите необходимые репозитории в __init__
    3. Реализуйте асинхронные методы бизнес-логики
    4. Добавьте документацию и типизацию
"""

from typing import Optional
from dataclasses import dataclass

from .base import BaseService
from database.database import Database
from database.repositories import UserRepository


@dataclass
class ProcessingResult:
    """
    Результат обработки данных.
    
    Attributes:
        success: Успешность операции
        message: Сообщение о результате
        data: Дополнительные данные (опционально)
    """
    success: bool
    message: str
    data: Optional[dict] = None


class ExampleService(BaseService):
    """
    Пример пользовательского сервиса.
    
    Демонстрирует структуру сервиса и основные паттерны реализации.
    
    Attributes:
        db: База данных
        user_repo: Репозиторий пользователей
    
    Example:
        >>> service = ExampleService(db)
        >>> result = await service.process_data("Hello")
        >>> print(result.message)
        'Обработано: Hello'
    """
    
    def __init__(self, db: Database):
        """
        Инициализация сервиса.
        
        Args:
            db: Экземпляр Database для работы с базой данных
        """
        super().__init__(db)
        self.user_repo = UserRepository(db)
    
    async def process_data(self, data: str) -> ProcessingResult:
        """
        Обработка входных данных.
        
        Пример метода бизнес-логики. В реальном сервисе здесь была бы
        более сложная логика с обращением к репозиториям и внешним API.
        
        Args:
            data: Входные данные для обработки
            
        Returns:
            ProcessingResult с результатом обработки
            
        Example:
            >>> result = await service.process_data("test")
            >>> assert result.success == True
        """
        # Пример валидации
        if not data:
            return ProcessingResult(
                success=False,
                message="Данные не могут быть пустыми"
            )
        
        # Пример обработки
        processed = data.upper()
        
        return ProcessingResult(
            success=True,
            message=f"Обработано: {processed}",
            data={"original": data, "processed": processed}
        )
    
    async def get_user_statistics(self, user_id: int) -> dict:
        """
        Получение статистики пользователя.
        
        Args:
            user_id: ID пользователя в базе данных
            
        Returns:
            Словарь со статистикой пользователя
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            return {"error": "Пользователь не найден"}
        
        return {
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "timezone": user.timezone,
            "is_admin": user.is_admin,
            "registered_at": str(user.created_at),
        }