"""
Регистрация всех обработчиков.
"""

from aiogram import Dispatcher

from .base import router as base_router
from .notes import router as notes_router
from .reminders import router as reminders_router
from .templates import router as templates_router
from .admin import router as admin_router
from .ai_chat import router as ai_chat_router


def setup_routers(dp: Dispatcher):
    """Регистрация всех роутеров в диспетчере."""
    dp.include_router(admin_router)
    dp.include_router(ai_chat_router)
    dp.include_router(notes_router)
    dp.include_router(reminders_router)
    dp.include_router(templates_router)
    dp.include_router(base_router)