"""
Регистрация всех обработчиков.
"""

from aiogram import Dispatcher

from .base import router as base_router
from .notes import router as notes_router
from .reminders import router as reminders_router
from .templates import router as templates_router
from .admin import router as admin_router


def setup_routers(dp: Dispatcher):
    """
    Регистрация всех роутеров в диспетчере.
    
    Порядок важен! Роутеры с фильтрами должны быть первыми.
    """
    # Административные функции (с фильтром IsAdmin) - ПЕРВЫМ
    dp.include_router(admin_router)
    
    # Основные функции
    dp.include_router(notes_router)
    dp.include_router(reminders_router)
    dp.include_router(templates_router)
    
    # Базовые обработчики - ПОСЛЕДНИМ (catch-all)
    dp.include_router(base_router)