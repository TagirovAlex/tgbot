"""
Базовый класс репозитория.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from database.database import Database


class BaseRepository(ABC):
    """
    Абстрактный базовый класс для всех репозиториев.
    
    Предоставляет общий интерфейс для CRUD операций.
    Все методы работают асинхронно.
    
    Attributes:
        db: Экземпляр Database для работы с БД
        table_name: Имя таблицы в базе данных
    
    Example:
        >>> class MyRepository(BaseRepository):
        ...     table_name = "my_table"
        ...     
        ...     async def create(self, **kwargs):
        ...         # Реализация создания записи
        ...         pass
    """
    
    table_name: str = ""
    
    def __init__(self, db: Database):
        self.db = db
    
    @abstractmethod
    async def create(self, **kwargs) -> int:
        """Создание записи. Возвращает ID созданной записи."""
        pass
    
    @abstractmethod
    async def get_by_id(self, record_id: int) -> Optional[Any]:
        """Получение записи по ID."""
        pass
    
    @abstractmethod
    async def update(self, record_id: int, **kwargs) -> bool:
        """Обновление записи. Возвращает True при успехе."""
        pass
    
    @abstractmethod
    async def delete(self, record_id: int) -> bool:
        """Удаление записи. Возвращает True при успехе."""
        pass
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> list:
        """Получение всех записей с пагинацией."""
        query = f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?"
        return await self.db.fetch_all(query, (limit, offset))