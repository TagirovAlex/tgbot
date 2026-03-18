"""
Сервис для выполнения скриптов на сервере.
"""

import asyncio
import logging
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

import config
from .base import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ScriptResult:
    """Результат выполнения скрипта."""
    script_name: str
    return_code: int
    stdout: str
    stderr: str
    success: bool


class ScriptRunnerService(BaseService):
    """
    Сервис для управления и выполнения скриптов.
    
    Позволяет администраторам просматривать доступные скрипты
    и запускать их на выполнение.
    """
    
    # Разрешённые расширения файлов
    ALLOWED_EXTENSIONS = {'.sh', '.bash', '.py', ''}
    
    def __init__(self, db, scripts_dir: Path = None):
        super().__init__(db)
        self.scripts_dir = scripts_dir or config.SCRIPTS_DIR
        
        # Создаём директорию если не существует
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_available_scripts(self) -> List[str]:
        """
        Получение списка доступных скриптов.
        
        Returns:
            Список имён файлов скриптов
        """
        scripts = []
        
        if not self.scripts_dir.exists():
            logger.warning(f"Директория скриптов не существует: {self.scripts_dir}")
            return scripts
        
        try:
            for file in self.scripts_dir.iterdir():
                if file.is_file() and not file.name.startswith('.'):
                    # Проверяем расширение
                    if file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                        scripts.append(file.name)
        except Exception as e:
            logger.error(f"Ошибка чтения директории скриптов: {e}")
        
        return sorted(scripts)
    
    async def run_script(
        self,
        script_name: str,
        timeout: int = 300
    ) -> ScriptResult:
        """
        Выполнение скрипта.
        
        Args:
            script_name: Имя скрипта для выполнения
            timeout: Таймаут выполнения в секундах
            
        Returns:
            ScriptResult с результатом выполнения
            
        Raises:
            FileNotFoundError: Если скрипт не найден
        """
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"Скрипт не найден: {script_name}")
        
        if not script_path.is_file():
            raise FileNotFoundError(f"Не является файлом: {script_name}")
        
        # Определяем команду для запуска
        suffix = script_path.suffix.lower()
        
        if suffix == '.py':
            cmd = ['python3', str(script_path)]
        elif suffix in ('.sh', '.bash'):
            cmd = ['bash', str(script_path)]
        else:
            # Пробуем запустить напрямую (если есть права на выполнение)
            if os.access(script_path, os.X_OK):
                cmd = [str(script_path)]
            else:
                # Пробуем через bash
                cmd = ['bash', str(script_path)]
        
        logger.info(f"Запуск скрипта: {script_name}, команда: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.scripts_dir)
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            result = ScriptResult(
                script_name=script_name,
                return_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                success=process.returncode == 0
            )
            
            logger.info(
                f"Скрипт {script_name} завершён с кодом {process.returncode}"
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Таймаут выполнения скрипта: {script_name}")
            return ScriptResult(
                script_name=script_name,
                return_code=-1,
                stdout="",
                stderr=f"Превышен таймаут выполнения ({timeout} сек)",
                success=False
            )
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта {script_name}: {e}")
            return ScriptResult(
                script_name=script_name,
                return_code=-1,
                stdout="",
                stderr=str(e),
                success=False
            )