"""
Регистрация всех обработчиков.

Этот модуль отвечает за подключение всех роутеров к диспетчеру.
Для добавления нового обработчика:
1. Создайте файл с роутером в этой директории
2. Импортируйте роутер ниже
3. Добавьте его в функцию setup_routers()
"""

from aiogram import Dispatcher

from .base import router as base_router
from .notes import router as notes_router
from .reminders import router as reminders_router
from .templates import router as templates_router
from .admin import router as admin_router
from .example_handler import router as example_router


def setup_routers(dp: Dispatcher):
    """
    Регистрация всех роутеров в диспетчере.
    
    Порядок регистрации важен! Роутеры проверяются в порядке добавления.
    Более специфичные роутеры должны быть добавлены раньше общих.
    
    Args:
        dp: Экземпляр Dispatcher
    """
    # Административные функции (проверяются первыми)
    dp.include_router(admin_router)
    
    # Основные функции
    dp.include_router(notes_router)
    dp.include_router(reminders_router)
    dp.include_router(templates_router)
    
    # Пример пользовательского обработчика
    dp.include_router(example_router)
    
    # Базовые обработчики (start, help, меню) - в конце
    dp.include_router(base_router)