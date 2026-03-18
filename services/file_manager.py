"""
Сервис для управления файлами.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from aiogram.types import Document, PhotoSize

import config
from .base import BaseService
from database.database import Database

logger = logging.getLogger(__name__)


class FileManagerService(BaseService):
    """
    Сервис для сохранения и управления файлами пользователей.
    
    Файлы сохраняются в подпапках по ID пользователя.
    """
    
    def __init__(self, db: Database, files_dir: Path = None):
        super().__init__(db)
        self.files_dir = files_dir or config.FILES_DIR
    
    def get_user_dir(self, user_id: int) -> Path:
        """Получение директории пользователя."""
        user_dir = self.files_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    async def save_file(
        self,
        bot,
        user_id: int,
        file_id: str,
        file_name: Optional[str] = None,
        file_type: str = "document"
    ) -> Path:
        """
        Сохранение файла от пользователя.
        
        Args:
            bot: Экземпляр бота
            user_id: ID пользователя (из БД)
            file_id: Telegram file_id
            file_name: Имя файла (опционально)
            file_type: Тип файла
            
        Returns:
            Путь к сохранённому файлу
        """
        user_dir = self.get_user_dir(user_id)
        
        # Получаем файл из Telegram
        file = await bot.get_file(file_id)
        
        # Генерируем имя файла если не указано
        if not file_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = Path(file.file_path).suffix if file.file_path else ""
            file_name = f"{file_type}_{timestamp}{extension}"
        
        # Путь для сохранения
        save_path = user_dir / file_name
        
        # Скачиваем и сохраняем
        await bot.download_file(file.file_path, save_path)
        
        # Логируем в БД
        await self._log_file_save(user_id, file_id, file_name, str(save_path), file_type)
        
        logger.info(f"Файл сохранён: {save_path}")
        return save_path
    
    async def _log_file_save(
        self,
        user_id: int,
        file_id: str,
        file_name: str,
        file_path: str,
        file_type: str
    ):
        """Логирование сохранения файла в БД."""
        await self.db.execute(
            """
            INSERT INTO received_files (user_id, file_id, file_name, file_path, file_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, file_id, file_name, file_path, file_type)
        )
    
    async def get_user_files(self, user_id: int) -> list[dict]:
        """Получение списка файлов пользователя."""
        rows = await self.db.fetch_all(
            """
            SELECT * FROM received_files 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        return [dict(row) for row in rows]
    
    def get_disk_usage(self, user_id: int) -> int:
        """Получение размера файлов пользователя в байтах."""
        user_dir = self.get_user_dir(user_id)
        total = 0
        for file in user_dir.rglob("*"):
            if file.is_file():
                total += file.stat().st_size
        return total