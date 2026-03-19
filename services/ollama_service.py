"""
Сервис для работы с Ollama LLM.

Ollama — это платформа для локального запуска больших языковых моделей.
Документация: https://github.com/ollama/ollama/blob/main/docs/api.md

Особенности:
- Администраторы могут управлять моделями
- Пользователи работают только с моделью, выбранной администратором
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import json

import aiohttp

import config
from .base import BaseService
from database.database import Database

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Сообщение в чате."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatSession:
    """Сессия чата с историей сообщений."""
    user_id: int
    messages: List[Message] = field(default_factory=list)
    system_prompt: Optional[str] = None
    model: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение в историю."""
        self.messages.append(Message(role=role, content=content))
        max_history = config.OLLAMA_MAX_HISTORY
        if len(self.messages) > max_history:
            if self.messages[0].role == "system":
                self.messages = [self.messages[0]] + self.messages[-(max_history-1):]
            else:
                self.messages = self.messages[-max_history:]
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Получить сообщения в формате API."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend([m.to_dict() for m in self.messages])
        return messages
    
    def clear(self):
        """Очистить историю."""
        self.messages.clear()


@dataclass
class GenerationResult:
    """Результат генерации."""
    success: bool
    content: str
    model: str = ""
    total_duration: float = 0.0
    prompt_tokens: int = 0
    response_tokens: int = 0
    error: Optional[str] = None


class OllamaService(BaseService):
    """
    Сервис для взаимодействия с Ollama LLM.
    
    Модель для пользователей устанавливается администратором и хранится в БД.
    """
    
    # Ключ для хранения активной модели в настройках
    ACTIVE_MODEL_KEY = "ollama_active_model"
    
    def __init__(
        self,
        db: Database,
        base_url: str = None,
        default_model: str = None,
        timeout: int = None
    ):
        super().__init__(db)
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self._default_model = default_model or config.OLLAMA_MODEL
        self.timeout = timeout or config.OLLAMA_TIMEOUT
        
        self._sessions: Dict[int, ChatSession] = {}
        
        self.system_prompts = {
            "default": (
                "Ты — полезный AI-ассистент. Отвечай кратко и по существу. "
                "Используй русский язык, если пользователь пишет на русском."
            ),
            "coding": (
                "Ты — опытный программист. Помогай с кодом, объясняй концепции, "
                "находи ошибки. Давай примеры кода с комментариями."
            ),
            "creative": (
                "Ты — креативный писатель. Помогай с текстами, историями, "
                "стихами. Будь творческим и оригинальным."
            ),
            "translator": (
                "Ты — профессиональный переводчик. Переводи тексты точно, "
                "сохраняя стиль и смысл оригинала."
            ),
        }
    
    async def get_active_model(self) -> str:
        """
        Получить активную модель из БД.
        Если не установлена — возвращает модель по умолчанию из конфига.
        """
        try:
            row = await self.db.fetch_one(
                "SELECT value FROM bot_settings WHERE key = ?",
                (self.ACTIVE_MODEL_KEY,)
            )
            if row and row["value"]:
                return row["value"]
        except Exception as e:
            logger.error(f"Error getting active model: {e}")
        
        return self._default_model
    
    async def set_active_model(self, model: str) -> bool:
        """
        Установить активную модель (только для админов).
        
        Args:
            model: Название модели
            
        Returns:
            True если успешно
        """
        try:
            # Проверяем что модель существует
            models = await self.list_models()
            model_names = [m.get("name", "") for m in models]
            
            if model not in model_names:
                logger.warning(f"Model {model} not found in available models")
                return False
            
            # Сохраняем в БД
            await self.db.execute(
                """
                INSERT INTO bot_settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (self.ACTIVE_MODEL_KEY, model)
            )
            
            # Очищаем все сессии при смене модели
            self._sessions.clear()
            
            logger.info(f"Active model set to: {model}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting active model: {e}")
            return False
    
    async def _request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """Выполнить запрос к Ollama API."""
        url = f"{self.base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    if stream:
                        return {"stream": response}
                    
                    return await response.json()
                    
        except asyncio.TimeoutError:
            raise Exception(f"Ollama request timeout ({self.timeout}s)")
        except aiohttp.ClientError as e:
            raise Exception(f"Ollama connection error: {e}")
    
    async def is_available(self) -> bool:
        """Проверить доступность Ollama сервера."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Скачать модель (только для админов).
        
        Args:
            model: Название модели для скачивания
            
        Yields:
            Статус загрузки
        """
        url = f"{self.base_url}/api/pull"
        data = {"name": model, "stream": True}
        
        try:
            timeout = aiohttp.ClientTimeout(total=3600)  # 1 час на загрузку
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error = await response.text()
                        yield {"error": error}
                        return
                    
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                yield chunk
                                
                                if chunk.get("status") == "success":
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            yield {"error": str(e)}
    
    async def delete_model(self, model: str) -> bool:
        """
        Удалить модель (только для админов).
        
        Args:
            model: Название модели
            
        Returns:
            True если успешно
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> GenerationResult:
        """Генерация текста (completion)."""
        if model is None:
            model = await self.get_active_model()
        
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            data["system"] = system
        
        data.update(kwargs)
        
        try:
            response = await self._request("/api/generate", data)
            
            return GenerationResult(
                success=True,
                content=response.get("response", ""),
                model=response.get("model", model),
                total_duration=response.get("total_duration", 0) / 1e9,
                prompt_tokens=response.get("prompt_eval_count", 0),
                response_tokens=response.get("eval_count", 0),
            )
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return GenerationResult(
                success=False,
                content="",
                error=str(e)
            )
    
    async def chat(
        self,
        user_id: int,
        message: str,
        model: str = None,
        mode: str = "default",
        temperature: float = 0.7,
        **kwargs
    ) -> GenerationResult:
        """Чат с сохранением истории."""
        if model is None:
            model = await self.get_active_model()
        
        session = self._get_or_create_session(user_id, model, mode)
        session.add_message("user", message)
        
        data = {
            "model": model,
            "messages": session.get_messages_for_api(),
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        data.update(kwargs)
        
        try:
            response = await self._request("/api/chat", data)
            
            assistant_message = response.get("message", {}).get("content", "")
            session.add_message("assistant", assistant_message)
            
            return GenerationResult(
                success=True,
                content=assistant_message,
                model=response.get("model", model),
                total_duration=response.get("total_duration", 0) / 1e9,
                prompt_tokens=response.get("prompt_eval_count", 0),
                response_tokens=response.get("eval_count", 0),
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            if session.messages and session.messages[-1].role == "user":
                session.messages.pop()
            
            return GenerationResult(
                success=False,
                content="",
                error=str(e)
            )
    
    async def chat_stream(
        self,
        user_id: int,
        message: str,
        model: str = None,
        mode: str = "default",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Чат со стримингом ответа."""
        if model is None:
            model = await self.get_active_model()
        
        session = self._get_or_create_session(user_id, model, mode)
        session.add_message("user", message)
        
        data = {
            "model": model,
            "messages": session.get_messages_for_api(),
            "stream": True,
        }
        data.update(kwargs)
        
        url = f"{self.base_url}/api/chat"
        full_response = ""
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as http_session:
                async with http_session.post(url, json=data) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise Exception(f"API error: {error}")
                    
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    full_response += content
                                    yield content
                                
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
            
            session.add_message("assistant", full_response)
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            if session.messages and session.messages[-1].role == "user":
                session.messages.pop()
            yield f"\n\n❌ Ошибка: {e}"
    
    def _get_or_create_session(
        self,
        user_id: int,
        model: str,
        mode: str = "default"
    ) -> ChatSession:
        """Получить или создать сессию чата."""
        if user_id not in self._sessions:
            system_prompt = self.system_prompts.get(mode, self.system_prompts["default"])
            self._sessions[user_id] = ChatSession(
                user_id=user_id,
                model=model,
                system_prompt=system_prompt
            )
        return self._sessions[user_id]
    
    def get_session(self, user_id: int) -> Optional[ChatSession]:
        """Получить сессию пользователя."""
        return self._sessions.get(user_id)
    
    def clear_session(self, user_id: int) -> bool:
        """Очистить историю чата пользователя."""
        if user_id in self._sessions:
            self._sessions[user_id].clear()
            return True
        return False
    
    def clear_all_sessions(self):
        """Очистить все сессии (при смене модели)."""
        self._sessions.clear()
    
    def delete_session(self, user_id: int) -> bool:
        """Удалить сессию пользователя."""
        if user_id in self._sessions:
            del self._sessions[user_id]
            return True
        return False
    
    def set_session_mode(self, user_id: int, mode: str) -> bool:
        """Установить режим чата."""
        if mode not in self.system_prompts:
            return False
        
        session = self._sessions.get(user_id)
        if session:
            session.system_prompt = self.system_prompts[mode]
            session.clear()
            return True
        return False
    
    def get_session_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о сессии."""
        session = self._sessions.get(user_id)
        if not session:
            return None
        
        return {
            "user_id": session.user_id,
            "model": session.model,
            "messages_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
        }


_ollama_service: Optional[OllamaService] = None


def get_ollama_service(db: Database = None) -> Optional[OllamaService]:
    """Получить экземпляр OllamaService."""
    global _ollama_service
    if _ollama_service is None and db is not None:
        _ollama_service = OllamaService(db)
    return _ollama_service


def init_ollama_service(db: Database) -> OllamaService:
    """Инициализировать OllamaService."""
    global _ollama_service
    _ollama_service = OllamaService(db)
    return _ollama_service