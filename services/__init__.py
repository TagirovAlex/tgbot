"""
Сервисы приложения.
"""

from .base import BaseService
from .scheduler import ReminderScheduler
from .script_runner import ScriptRunnerService
from .file_manager import FileManagerService
from .example_service import ExampleService
from .ollama_service import (
    OllamaService,
    ChatSession,
    Message,
    GenerationResult,
    get_ollama_service,
    init_ollama_service,
)

__all__ = [
    "BaseService",
    "ReminderScheduler",
    "ScriptRunnerService",
    "FileManagerService",
    "ExampleService",
    "OllamaService",
    "ChatSession",
    "Message",
    "GenerationResult",
    "get_ollama_service",
    "init_ollama_service",
]