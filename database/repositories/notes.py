"""
Репозиторий для работы с заметками.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .base import BaseRepository


@dataclass
class Note:
    """Модель заметки."""
    id: int
    user_id: int
    title: str
    content: Optional[str]
    created_at: datetime
    updated_at: datetime


class NoteRepository(BaseRepository):
    """Репозиторий для работы с заметками."""
    
    table_name = "notes"
    
    def _row_to_note(self, row) -> Optional[Note]:
        """Преобразование строки БД в объект Note."""
        if not row:
            return None
        return Note(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    async def create(
        self,
        user_id: int,
        title: str,
        content: Optional[str] = None,
    ) -> int:
        """Создание заметки."""
        cursor = await self.db.execute(
            """
            INSERT INTO notes (user_id, title, content)
            VALUES (?, ?, ?)
            """,
            (user_id, title, content)
        )
        return cursor.lastrowid
    
    async def get_by_id(self, note_id: int) -> Optional[Note]:
        """Получение заметки по ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM notes WHERE id = ?",
            (note_id,)
        )
        return self._row_to_note(row)
    
    async def get_user_notes(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[Note]:
        """Получение заметок пользователя."""
        rows = await self.db.fetch_all(
            """
            SELECT * FROM notes 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        return [self._row_to_note(row) for row in rows]
    
    async def update(
        self,
        note_id: int,
        **kwargs
    ) -> bool:
        """Обновление заметки."""
        if not kwargs:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [note_id]
        
        await self.db.execute(
            f"UPDATE notes SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )
        return True
    
    async def delete(self, note_id: int) -> bool:
        """Удаление заметки."""
        await self.db.execute(
            "DELETE FROM notes WHERE id = ?",
            (note_id,)
        )
        return True
    
    async def search(
        self,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> list[Note]:
        """Поиск заметок по тексту."""
        rows = await self.db.fetch_all(
            """
            SELECT * FROM notes 
            WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, f"%{query}%", f"%{query}%", limit)
        )
        return [self._row_to_note(row) for row in rows]
    
    async def count_user_notes(self, user_id: int) -> int:
        """Подсчёт количества заметок пользователя."""
        row = await self.db.fetch_one(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ?",
            (user_id,)
        )
        return row["count"] if row else 0