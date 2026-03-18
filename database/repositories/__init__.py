"""
Репозитории для работы с данными.
"""

from .base import BaseRepository
from .users import UserRepository
from .notes import NoteRepository
from .reminders import ReminderRepository
from .templates import TemplateRepository

__all__ = [
    "BaseRepository",
    "UserRepository", 
    "NoteRepository",
    "ReminderRepository",
    "TemplateRepository",
]