"""
Middleware бота.
"""

from aiogram import Dispatcher

from database.database import Database
from .logging_middleware import LoggingMiddleware
from .auth import AuthMiddleware


def setup_middlewares(dp: Dispatcher, db: Database):
    """Настройка всех middleware."""
    # Порядок важен: auth должен быть первым
    dp.message.middleware(AuthMiddleware(db))
    dp.callback_query.middleware(AuthMiddleware(db))
    
    dp.message.middleware(LoggingMiddleware(db))
    dp.callback_query.middleware(LoggingMiddleware(db))