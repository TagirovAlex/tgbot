"""
Репозиторий для работы с напоминаниями.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .base import BaseRepository


@dataclass
class Reminder:
    """Модель напоминания."""
    id: int
    user_id: int
    chat_id: int
    title: str
    content: Optional[str]
    remind_at: datetime
    repeat_interval: int  # в минутах, 0 = одноразовое
    is_group: bool
    is_active: bool
    last_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ReminderRepository(BaseRepository):
    """Репозиторий для работы с напоминаниями."""
    
    table_name = "reminders"
    
    def _row_to_reminder(self, row) -> Optional[Reminder]:
        """Преобразование строки БД в объект Reminder."""
        if not row:
            return None
        return Reminder(
            id=row["id"],
            user_id=row["user_id"],
            chat_id=row["chat_id"],
            title=row["title"],
            content=row["content"],
            remind_at=row["remind_at"],
            repeat_interval=row["repeat_interval"],
            is_group=bool(row["is_group"]),
            is_active=bool(row["is_active"]),
            last_sent_at=row["last_sent_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    async def create(
        self,
        user_id: int,
        chat_id: int,
        title: str,
        remind_at: datetime,
        content: Optional[str] = None,
        repeat_interval: int = 0,
        is_group: bool = False,
    ) -> int:
        """Создание напоминания."""
        cursor = await self.db.execute(
            """
            INSERT INTO reminders 
            (user_id, chat_id, title, content, remind_at, repeat_interval, is_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, chat_id, title, content, remind_at, repeat_interval, int(is_group))
        )
        return cursor.lastrowid
    
    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """Получение напоминания по ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        return self._row_to_reminder(row)
    
    async def get_user_reminders(
        self,
        user_id: int,
        active_only: bool = True,
        limit: int = 50
    ) -> list[Reminder]:
        """Получение напоминаний пользователя."""
        query = """
            SELECT * FROM reminders 
            WHERE user_id = ?
        """
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY remind_at ASC LIMIT ?"
        
        rows = await self.db.fetch_all(query, (user_id, limit))
        return [self._row_to_reminder(row) for row in rows]
    
    async def get_pending_reminders(self, until: datetime) -> list[Reminder]:
        """
        Получение активных напоминаний, которые нужно отправить.
        
        Args:
            until: Время, до которого искать напоминания (UTC)
        """
        rows = await self.db.fetch_all(
            """
            SELECT * FROM reminders 
            WHERE is_active = 1 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (until,)
        )
        return [self._row_to_reminder(row) for row in rows]
    
    async def update(
        self,
        reminder_id: int,
        **kwargs
    ) -> bool:
        """Обновление напоминания."""
        if not kwargs:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [reminder_id]
        
        await self.db.execute(
            f"UPDATE reminders SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )
        return True
    
    async def delete(self, reminder_id: int) -> bool:
        """Удаление напоминания."""
        await self.db.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        return True
    
    async def deactivate(self, reminder_id: int) -> bool:
        """Деактивация напоминания."""
        return await self.update(reminder_id, is_active=0)
    
    async def mark_sent(self, reminder_id: int, next_remind_at: Optional[datetime] = None) -> bool:
        """
        Отметить напоминание как отправленное.
        Если указано next_remind_at, обновляет время следующего напоминания.
        """
        if next_remind_at:
            return await self.update(
                reminder_id,
                last_sent_at=datetime.utcnow(),
                remind_at=next_remind_at
            )
        else:
            return await self.update(
                reminder_id,
                last_sent_at=datetime.utcnow(),
                is_active=0
            )