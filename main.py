"""
Главный файл запуска бота.
"""

import asyncio
import logging
import sys
import signal
from contextlib import suppress
from typing import Optional

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
        logging.FileHandler(config.LOGS_DIR / "bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Глобальная переменная для доступа к приложению
_bot_app_instance: Optional["BotApplication"] = None


def get_bot_app() -> Optional["BotApplication"]:
    """Получение текущего экземпляра приложения."""
    return _bot_app_instance


def set_bot_app(app: Optional["BotApplication"]):
    """Установка экземпляра приложения."""
    global _bot_app_instance
    _bot_app_instance = app


class BotApplication:
    """Основной класс приложения бота."""
    
    def __init__(self):
        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.db = Database(config.DATABASE_PATH)
        self.scheduler: Optional[ReminderScheduler] = None
        self._shutdown_event = asyncio.Event()
        self._restart_requested = False
        self._is_running = False
        
        # Сохраняем глобально для доступа из обработчиков
        set_bot_app(self)
    
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
        if not self._is_running:
            return
            
        self._is_running = False
        logger.info("Завершение работы бота...")
        
        # Останавливаем планировщик
        if self.scheduler:
            try:
                await self.scheduler.stop()
            except Exception as e:
                logger.error(f"Ошибка остановки планировщика: {e}")
        
        # Закрываем базу данных
        try:
            await self.db.close()
        except Exception as e:
            logger.error(f"Ошибка закрытия БД: {e}")
        
        # Закрываем сессию бота
        try:
            await self.bot.session.close()
        except Exception as e:
            logger.error(f"Ошибка закрытия сессии бота: {e}")
        
        # Очищаем глобальную ссылку
        set_bot_app(None)
        
        logger.info("Бот остановлен")
    
    def request_shutdown(self):
        """Запрос на завершение работы."""
        logger.info("Получен запрос на завершение...")
        self._shutdown_event.set()
    
    async def restart(self):
        """Перезапуск бота."""
        logger.info("Запрошен перезапуск бота...")
        self._restart_requested = True
        self._shutdown_event.set()
    
    async def run(self) -> bool:
        """
        Запуск бота.
        
        Returns:
            True если нужен перезапуск, False если обычное завершение
        """
        self._is_running = True
        
        try:
            await self.setup()
            logger.info("Бот запущен и готов к работе")
            
            # Запускаем polling
            polling_task = asyncio.create_task(
                self.dp.start_polling(
                    self.bot,
                    handle_signals=False  # Отключаем встроенную обработку сигналов
                )
            )
            
            # Ждём сигнал завершения
            await self._shutdown_event.wait()
            
            # Останавливаем polling
            logger.info("Остановка polling...")
            polling_task.cancel()
            
            with suppress(asyncio.CancelledError):
                await polling_task
                
        except asyncio.CancelledError:
            logger.info("Получен сигнал отмены")
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {e}", exc_info=True)
        finally:
            await self.shutdown()
        
        return self._restart_requested


async def main():
    """Точка входа."""
    loop = asyncio.get_running_loop()
    
    # Создаём приложение
    app = BotApplication()
    
    # Обработчик сигналов завершения
    def signal_handler(sig):
        logger.info(f"Получен сигнал {sig.name}")
        app.request_shutdown()
    
    # Регистрируем обработчики сигналов
    # Для Windows используем другой подход
    if sys.platform != 'win32':
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    restart = True
    
    while restart:
        try:
            restart = await app.run()
            
            if restart:
                logger.info("Перезапуск через 2 секунды...")
                await asyncio.sleep(2)
                # Создаём новый экземпляр для перезапуска
                app = BotApplication()
        except asyncio.CancelledError:
            logger.info("Главная задача отменена")
            restart = False
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            restart = False


def run_bot():
    """Запуск бота с обработкой сигналов для Windows."""
    if sys.platform == 'win32':
        # Для Windows используем специальный подход
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except SystemExit:
        logger.info("Системный выход")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}", exc_info=True)
    finally:
        logger.info("Программа завершена")


if __name__ == "__main__":
    run_bot()