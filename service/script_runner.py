"""
Сервис для выполнения скриптов на сервере.
"""

import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

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
    
    def __init__(self, db, scripts_dir: Path = None):
        super().__init__(db)
        self.scripts_dir = scripts_dir or config.SCRIPTS_DIR
    
    async def get_available_scripts(self) -> list[str]:
        """
        Получение списка доступных скриптов.
        
        Returns:
            Список имён файлов скриптов
        """
        scripts = []
        
        if not self.scripts_dir.exists():
            return scripts
        
        for file in self.scripts_dir.iterdir():
            if file.is_file() and not file.name.startswith('.'):
                # Проверяем расширение
                if file.suffix in ('.sh', '.py', '.bash', ''):
                    scripts.append(file.name)
        
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
            asyncio.TimeoutError: Если превышен таймаут
        """
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"Скрипт не найден: {script_name}")
        
        # Определяем команду для запуска
        if script_path.suffix == '.py':
            cmd = ['python', str(script_path)]
        elif script_path.suffix in ('.sh', '.bash'):
            cmd = ['bash', str(script_path)]
        else:
            # Пробуем запустить напрямую
            cmd = [str(script_path)]
        
        logger.info(f"Запуск скрипта: {script_name}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
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