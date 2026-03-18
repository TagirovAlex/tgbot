"""
Репозиторий для работы с пользователями.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .base import BaseRepository


@dataclass
class User:
    """Модель пользователя."""
    id: int
    telegram_id: int
    username: Optional[str]
    full_name: Optional[str]
    timezone: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""
    
    table_name = "users"
    
    def _row_to_user(self, row) -> Optional[User]:
        """Преобразование строки БД в объект User."""
        if not row:
            return None
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            full_name=row["full_name"],
            timezone=row["timezone"],
            is_admin=bool(row["is_admin"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        timezone: str = "UTC",
        is_admin: bool = False,
    ) -> int:
        """Создание пользователя."""
        cursor = await self.db.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, timezone, is_admin)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_id, username, full_name, timezone, int(is_admin))
        )
        return cursor.lastrowid
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        return self._row_to_user(row)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return self._row_to_user(row)
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Получение или создание пользователя."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем данные пользователя
            await self.update(
                user.id,
                username=username,
                full_name=full_name
            )
            return await self.get_by_id(user.id)
        
        user_id = await self.create(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        return await self.get_by_id(user_id)
    
    async def update(
        self,
        user_id: int,
        **kwargs
    ) -> bool:
        """Обновление данных пользователя."""
        if not kwargs:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id]
        
        await self.db.execute(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )
        return True
    
    async def delete(self, user_id: int) -> bool:
        """Удаление пользователя."""
        await self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        return True
    
    async def set_admin(self, user_id: int, is_admin: bool) -> bool:
        """Установка прав администратора."""
        return await self.update(user_id, is_admin=int(is_admin))
    
    async def set_timezone(self, user_id: int, timezone: str) -> bool:
        """Установка часового пояса."""
        return await self.update(user_id, timezone=timezone)
    
    async def get_all_users(self) -> list[User]:
        """Получение списка всех пользователей."""
        rows = await self.db.fetch_all("SELECT * FROM users ORDER BY created_at DESC")
        return [self._row_to_user(row) for row in rows]
    
    async def get_admins(self) -> list[User]:
        """Получение списка администраторов."""
        rows = await self.db.fetch_all(
            "SELECT * FROM users WHERE is_admin = 1"
        )
        return [self._row_to_user(row) for row in rows]