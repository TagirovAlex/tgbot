"""
Планировщик напоминаний.

Использует нативные возможности asyncio для планирования задач.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot

from database.database import Database
from database.repositories import ReminderRepository

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Планировщик для отправки напоминаний.
    
    Работает в фоновом режиме, периодически проверяя наличие
    напоминаний, которые нужно отправить.
    
    Attributes:
        bot: Экземпляр бота для отправки сообщений
        db: База данных
        check_interval: Интервал проверки напоминаний (секунды)
    """
    
    def __init__(
        self,
        bot: Bot,
        db: Database,
        check_interval: int = 30
    ):
        self.bot = bot
        self.db = db
        self.reminder_repo = ReminderRepository(db)
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Запуск планировщика."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Планировщик напоминаний запущен")
    
    async def stop(self):
        """Остановка планировщика."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик напоминаний остановлен")
    
    async def _run_loop(self):
        """Основной цикл проверки напоминаний."""
        while self._running:
            try:
                await self._check_and_send_reminders()
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_send_reminders(self):
        """Проверка и отправка напоминаний."""
        now = datetime.utcnow()
        reminders = await self.reminder_repo.get_pending_reminders(now)
        
        for reminder in reminders:
            try:
                await self._send_reminder(reminder)
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания {reminder.id}: {e}")
    
    async def _send_reminder(self, reminder):
        """Отправка одного напоминания."""
        # Формируем сообщение
        message = f"🔔 <b>Напоминание:</b> {reminder.title}"
        if reminder.content:
            message += f"\n\n{reminder.content}"
        
        # Отправляем
        await self.bot.send_message(
            chat_id=reminder.chat_id,
            text=message
        )
        
        logger.info(f"Напоминание {reminder.id} отправлено в чат {reminder.chat_id}")
        
        # Обновляем статус
        if reminder.repeat_interval > 0:
            # Повторяемое напоминание - вычисляем следующее время
            next_time = datetime.utcnow() + timedelta(minutes=reminder.repeat_interval)
            await self.reminder_repo.mark_sent(reminder.id, next_remind_at=next_time)
            logger.info(f"Следующее напоминание {reminder.id} запланировано на {next_time}")
        else:
            # Одноразовое напоминание - деактивируем
            await self.reminder_repo.mark_sent(reminder.id)