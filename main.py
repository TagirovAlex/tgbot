"""
Главный файл запуска бота.
"""

import asyncio
import logging
import sys
import signal
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from database.database import Database
from services.scheduler import ReminderScheduler
from bot.handlers import setup_routers
from bot.middlewares import setup_middlewares


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BotApplication:
    """Основной класс приложения бота."""
    
    def __init__(self):
        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.db = Database(config.DATABASE_PATH)
        self.scheduler: ReminderScheduler | None = None
        self._shutdown_event = asyncio.Event()
    
    async def setup(self):
        """Инициализация компонентов."""
        # Инициализация базы данных
        await self.db.init()
        logger.info("База данных инициализирована")
        
        # Сохраняем ссылки в dp для доступа из handlers
        self.dp["db"] = self.db
        self.dp["bot_app"] = self
        
        # Настройка middleware
        setup_middlewares(self.dp, self.db)
        logger.info("Middleware настроены")
        
        # Настройка роутеров
        setup_routers(self.dp)
        logger.info("Роутеры настроены")
        
        # Запуск планировщика напоминаний
        self.scheduler = ReminderScheduler(self.bot, self.db)
        asyncio.create_task(self.scheduler.start())
        logger.info("Планировщик напоминаний запущен")
    
    async def shutdown(self):
        """Корректное завершение работы."""
        logger.info("Завершение работы бота...")
        
        if self.scheduler:
            await self.scheduler.stop()
        
        await self.db.close()
        await self.bot.session.close()
        
        logger.info("Бот остановлен")
    
    async def restart(self):
        """Перезапуск бота."""
        logger.info("Перезапуск бота...")
        self._shutdown_event.set()
    
    async def run(self):
        """Запуск бота."""
        await self.setup()
        
        try:
            logger.info("Бот запущен")
            
            # Запускаем polling в отдельной задаче
            polling_task = asyncio.create_task(
                self.dp.start_polling(self.bot)
            )
            
            # Ждём сигнал завершения
            await self._shutdown_event.wait()
            
            # Останавливаем polling
            polling_task.cancel()
            with suppress(asyncio.CancelledError):
                await polling_task
                
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()


async def main():
    """Точка входа."""
    app = BotApplication()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")