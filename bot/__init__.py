"""
Модуль бота.
"""

from .handlers import setup_routers
from .middlewares import setup_middlewares

__all__ = ["setup_routers", "setup_middlewares"]