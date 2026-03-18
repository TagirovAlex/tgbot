"""
Репозиторий для работы с напоминаниями.
"""

from typing import Optional, List
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
    remind_at: datetime  # Может быть строкой из SQLite
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
        **kwargs  # Для совместимости с базовым классом
    ) -> int:
        """Создание напоминания."""
        # Преобразуем datetime в строку для SQLite
        remind_at_str = remind_at.strftime("%Y-%m-%d %H:%M:%S")
        
        cursor = await self.db.execute(
            """
            INSERT INTO reminders 
            (user_id, chat_id, title, content, remind_at, repeat_interval, is_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, chat_id, title, content, remind_at_str, repeat_interval, int(is_group))
        )
        return cursor.lastrowid
    
    async def get_by_id(self, record_id: int) -> Optional[Reminder]:
        """Получение напоминания по ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM reminders WHERE id = ?",
            (record_id,)
        )
        return self._row_to_reminder(row)
    
    async def update(self, record_id: int, **kwargs) -> bool:
        """Обновление напоминания."""
        if not kwargs:
            return False
        
        # Обрабатываем специальные значения
        processed_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                # Преобразуем datetime в строку
                processed_kwargs[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                processed_kwargs[key] = value
        
        set_clause = ", ".join(f"{k} = ?" for k in processed_kwargs.keys())
        values = list(processed_kwargs.values()) + [record_id]
        
        await self.db.execute(
            f"UPDATE reminders SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )
        return True
    
    async def delete(self, record_id: int) -> bool:
        """Удаление напоминания."""
        await self.db.execute(
            "DELETE FROM reminders WHERE id = ?",
            (record_id,)
        )
        return True
    
    async def get_user_reminders(
        self,
        user_id: int,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Reminder]:
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
    
    async def get_pending_reminders(self, until: datetime) -> List[Reminder]:
        """
        Получение активных напоминаний, которые нужно отправить.
        
        Args:
            until: Время, до которого искать напоминания (UTC)
        """
        until_str = until.strftime("%Y-%m-%d %H:%M:%S")
        
        rows = await self.db.fetch_all(
            """
            SELECT * FROM reminders 
            WHERE is_active = 1 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (until_str,)
        )
        return [self._row_to_reminder(row) for row in rows]
    
    async def deactivate(self, reminder_id: int) -> bool:
        """Деактивация напоминания."""
        return await self.update(reminder_id, is_active=0)
    
    async def activate(self, reminder_id: int) -> bool:
        """Активация напоминания."""
        return await self.update(reminder_id, is_active=1)
    
    async def mark_sent(self, reminder_id: int, next_remind_at: Optional[datetime] = None) -> bool:
        """
        Отметить напоминание как отправленное.
        Если указано next_remind_at, обновляет время следующего напоминания.
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        if next_remind_at:
            next_str = next_remind_at.strftime("%Y-%m-%d %H:%M:%S")
            return await self.update(
                reminder_id,
                last_sent_at=now_str,
                remind_at=next_str
            )
        else:
            return await self.update(
                reminder_id,
                last_sent_at=now_str,
                is_active=0
            )
    
    async def count_user_reminders(self, user_id: int, active_only: bool = True) -> int:
        """Подсчёт количества напоминаний пользователя."""
        query = "SELECT COUNT(*) as count FROM reminders WHERE user_id = ?"
        if active_only:
            query += " AND is_active = 1"
        
        row = await self.db.fetch_one(query, (user_id,))
        return row["count"] if row else 0