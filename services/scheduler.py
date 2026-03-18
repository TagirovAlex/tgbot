"""
Планировщик напоминаний.

Использует нативные возможности asyncio для планирования задач.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from database.database import Database
from database.repositories import ReminderRepository
from utils.timezone import ensure_datetime

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Планировщик для отправки напоминаний.
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
        self._stop_event = asyncio.Event()
    
    async def start(self):
        """Запуск планировщика."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Планировщик напоминаний запущен")
    
    async def stop(self):
        """Остановка планировщика."""
        if not self._running:
            return
            
        logger.info("Остановка планировщика напоминаний...")
        self._running = False
        self._stop_event.set()
        
        if self._task:
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._task = None
        
        logger.info("Планировщик напоминаний остановлен")
    
    async def _run_loop(self):
        """Основной цикл проверки напоминаний."""
        while self._running:
            try:
                await self._check_and_send_reminders()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}", exc_info=True)
            
            # Ждём с возможностью прерывания
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.check_interval
                )
                # Если дождались события - выходим
                break
            except asyncio.TimeoutError:
                # Таймаут - продолжаем цикл
                continue
    
    async def _check_and_send_reminders(self):
        """Проверка и отправка напоминаний."""
        if not self._running:
            return
            
        now = datetime.utcnow()
        
        try:
            reminders = await self.reminder_repo.get_pending_reminders(now)
        except Exception as e:
            logger.error(f"Ошибка получения напоминаний: {e}")
            return
        
        for reminder in reminders:
            if not self._running:
                break
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
        try:
            await self.bot.send_message(
                chat_id=reminder.chat_id,
                text=message
            )
            logger.info(f"Напоминание {reminder.id} отправлено в чат {reminder.chat_id}")
        except TelegramAPIError as e:
            logger.error(f"Telegram API ошибка для напоминания {reminder.id}: {e}")
            # Если чат недоступен, деактивируем напоминание
            if "chat not found" in str(e).lower() or "bot was blocked" in str(e).lower():
                await self.reminder_repo.deactivate(reminder.id)
                logger.info(f"Напоминание {reminder.id} деактивировано (чат недоступен)")
            return
        except Exception as e:
            logger.error(f"Не удалось отправить напоминание {reminder.id}: {e}")
            return
        
        # Обновляем статус
        if reminder.repeat_interval > 0:
            # Повторяемое напоминание - вычисляем следующее время
            remind_at = ensure_datetime(reminder.remind_at) or datetime.utcnow()
            next_time = remind_at + timedelta(minutes=reminder.repeat_interval)
            await self.reminder_repo.mark_sent(reminder.id, next_remind_at=next_time)
            logger.info(f"Следующее напоминание {reminder.id} запланировано на {next_time}")
        else:
            # Одноразовое напоминание - деактивируем
            await self.reminder_repo.mark_sent(reminder.id)
            logger.info(f"Напоминание {reminder.id} выполнено и деактивировано")