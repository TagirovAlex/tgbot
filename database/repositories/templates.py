"""
Репозиторий для работы с шаблонами.
"""

from typing import Optional, Literal, List
from dataclasses import dataclass
from datetime import datetime

from .base import BaseRepository


TemplateType = Literal["note", "reminder"]


@dataclass
class Template:
    """Модель шаблона."""
    id: int
    user_id: int
    name: str
    type: TemplateType
    title_template: Optional[str]
    content_template: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    def apply(self, **variables) -> tuple[str, str]:
        """
        Применение шаблона с подстановкой переменных.
        
        Args:
            **variables: Переменные для подстановки
            
        Returns:
            Tuple (title, content) с подставленными значениями
        """
        title = self.title_template or ""
        content = self.content_template or ""
        
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            title = title.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))
        
        return title, content


class TemplateRepository(BaseRepository):
    """Репозиторий для работы с шаблонами."""
    
    table_name = "templates"
    
    def _row_to_template(self, row) -> Optional[Template]:
        """Преобразование строки БД в объект Template."""
        if not row:
            return None
        return Template(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            type=row["type"],
            title_template=row["title_template"],
            content_template=row["content_template"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    async def create(
        self,
        user_id: int,
        name: str,
        template_type: TemplateType,
        title_template: Optional[str] = None,
        content_template: Optional[str] = None,
        **kwargs
    ) -> int:
        """Создание шаблона."""
        cursor = await self.db.execute(
            """
            INSERT INTO templates (user_id, name, type, title_template, content_template)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, template_type, title_template, content_template)
        )
        return cursor.lastrowid
    
    async def get_by_id(self, record_id: int) -> Optional[Template]:
        """Получение шаблона по ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM templates WHERE id = ?",
            (record_id,)
        )
        return self._row_to_template(row)
    
    async def update(self, record_id: int, **kwargs) -> bool:
        """Обновление шаблона."""
        if not kwargs:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [record_id]
        
        await self.db.execute(
            f"UPDATE templates SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )
        return True
    
    async def delete(self, record_id: int) -> bool:
        """Удаление шаблона."""
        await self.db.execute(
            "DELETE FROM templates WHERE id = ?",
            (record_id,)
        )
        return True
    
    async def get_user_templates(
        self,
        user_id: int,
        template_type: Optional[TemplateType] = None,
        limit: int = 50
    ) -> List[Template]:
        """Получение шаблонов пользователя."""
        if template_type:
            rows = await self.db.fetch_all(
                """
                SELECT * FROM templates 
                WHERE user_id = ? AND type = ?
                ORDER BY name ASC
                LIMIT ?
                """,
                (user_id, template_type, limit)
            )
        else:
            rows = await self.db.fetch_all(
                """
                SELECT * FROM templates 
                WHERE user_id = ?
                ORDER BY type, name ASC
                LIMIT ?
                """,
                (user_id, limit)
            )
        return [self._row_to_template(row) for row in rows]