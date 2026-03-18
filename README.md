# Telegram Assistant Bot

Многофункциональный Telegram-бот для управления заметками, напоминаниями, выполнения административных задач и общения с AI через Ollama LLM.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)
![Ollama](https://img.shields.io/badge/Ollama-LLM-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Содержание

- [Возможности](#возможности)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [Использование](#использование)
- [Структура проекта](#структура-проекта)
- [Расширение функционала](#расширение-функционала)
- [Архитектура](#архитектура)
- [Используемые библиотеки](#используемые-библиотеки)
- [Лицензия](#лицензия)

## Возможности

### Для всех пользователей

**Заметки** — создание, редактирование, удаление, просмотр списка заметок с поддержкой шаблонов.

**Напоминания** — личные и групповые напоминания с поддержкой повторения: ежечасно, ежедневно, еженедельно, ежемесячно. Автоматический учёт часового пояса пользователя.

**Шаблоны** — создание шаблонов для быстрого создания заметок и напоминаний с поддержкой переменных (имя, дата, время).

**AI Ассистент** — общение с локальной языковой моделью через Ollama. Поддержка нескольких режимов: обычный, программист, креативный, переводчик. Сохранение контекста беседы.

**Часовые пояса** — настройка персонального часового пояса для корректного отображения времени напоминаний.

### Для администраторов

**Управление пользователями** — просмотр списка всех пользователей, назначение и снятие прав администратора.

**Выполнение скриптов** — запуск bash и python скриптов на сервере через меню бота с отображением результата выполнения.

**Логи действий** — просмотр истории действий всех пользователей бота.

**Перезапуск бота** — удалённый перезапуск через команду или меню без доступа к серверу.

**Управление файлами** — автоматическое сохранение полученных от пользователей файлов с разбивкой по директориям.

## Требования

- Python 3.10 или выше
- pip (менеджер пакетов Python)
- SQLite 3 (встроен в Python)
- Ollama (опционально, для AI функций)

## Установка

Клонируйте репозиторий:

    git clone https://github.com/yourusername/telegram-assistant-bot.git
    cd telegram-assistant-bot

Создайте виртуальное окружение:

    python3 -m venv venv
    source venv/bin/activate

Для Windows используйте:

    venv\Scripts\activate

Установите зависимости:

    pip install -r requirements.txt

Создайте файл конфигурации:

    cp .env.example .env

Отредактируйте .env файл и укажите токен бота и ID администраторов.

### Установка Ollama (опционально)

Для Linux:

    curl -fsSL https://ollama.com/install.sh | sh

Для macOS:

    brew install ollama

Запуск сервера Ollama:

    ollama serve

Скачивание модели (в другом терминале):

    ollama pull llama3.2

Проверка установленных моделей:

    ollama list

## Конфигурация

Содержимое файла .env:

    # Telegram Bot Token (получить у @BotFather)
    BOT_TOKEN=your_bot_token_here
    
    # ID администраторов через запятую (узнать свой ID: @userinfobot)
    ADMIN_IDS=123456789,987654321
    
    # Путь к базе данных
    DATABASE_PATH=database.db
    
    # Директории
    SCRIPTS_DIR=scripts
    FILES_DIR=storage/files
    LOGS_DIR=logs
    
    # Часовой пояс сервера
    SERVER_TIMEZONE=UTC
    
    # Ollama LLM Settings
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=llama3.2
    OLLAMA_TIMEOUT=120
    OLLAMA_MAX_HISTORY=10

### Получение BOT_TOKEN

1. Откройте @BotFather в Telegram
2. Отправьте команду /newbot
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в файл .env

### Получение ADMIN_IDS

1. Откройте @userinfobot в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш ID в файл .env

## Запуск

### Локальный запуск

    source venv/bin/activate
    python main.py

### Запуск как systemd сервис (Linux)

Создайте файл сервиса:

    sudo nano /etc/systemd/system/telegram-bot.service

Содержимое файла:

    [Unit]
    Description=Telegram Assistant Bot
    After=network.target
    
    [Service]
    Type=simple
    User=your_username
    Group=your_username
    WorkingDirectory=/path/to/telegram-assistant-bot
    ExecStart=/path/to/telegram-assistant-bot/venv/bin/python main.py
    Restart=on-failure
    RestartSec=10
    TimeoutStopSec=30
    KillMode=mixed
    KillSignal=SIGTERM
    EnvironmentFile=/path/to/telegram-assistant-bot/.env
    
    [Install]
    WantedBy=multi-user.target

Замените your_username на имя пользователя и /path/to/telegram-assistant-bot на путь к проекту.

Активация и запуск сервиса:

    sudo systemctl daemon-reload
    sudo systemctl enable telegram-bot
    sudo systemctl start telegram-bot

Проверка статуса:

    sudo systemctl status telegram-bot

Просмотр логов:

    sudo journalctl -u telegram-bot -f

## Использование

### Основные команды

| Команда | Описание |
|---------|----------|
| /start | Открыть главное меню |
| /help | Показать справку по командам |
| /notes | Управление заметками |
| /reminders | Управление напоминаниями |
| /remind текст | Быстрое создание напоминания |
| /templates | Управление шаблонами |
| /timezone | Настройка часового пояса |
| /ai | Открыть меню AI ассистента |
| /ai вопрос | Быстрый вопрос к AI |
| /ai_models | Список доступных моделей AI |
| /ai_clear | Очистить историю чата с AI |

### Команды администратора

| Команда | Описание |
|---------|----------|
| /admin | Открыть панель администратора |
| /users | Показать список пользователей |
| /scripts | Показать список доступных скриптов |
| /logs | Показать последние действия пользователей |
| /restart | Перезапустить бота |

### Создание напоминания в группе

1. Добавьте бота в группу
2. Дайте боту права на отправку сообщений
3. Напишите в группе: /remind Текст напоминания
4. Укажите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ
5. Выберите интервал повтора из предложенных вариантов

### Использование шаблонов

Шаблоны поддерживают следующие переменные:

| Переменная | Описание |
|------------|----------|
| {{name}} | Имя пользователя |
| {{date}} | Текущая дата в формате ДД.ММ.ГГГГ |
| {{time}} | Текущее время в формате ЧЧ:ММ |

Пример шаблона заголовка: Заметка от {{date}} - {{name}}

### Режимы AI ассистента

| Режим | Описание |
|-------|----------|
| Обычный | Универсальный помощник для общих вопросов |
| Программист | Помощь с кодом, отладка, объяснение концепций |
| Креативный | Написание текстов, историй, стихов |
| Переводчик | Перевод текстов между языками |

## Структура проекта

    telegram-assistant-bot/
    ├── main.py
    ├── config.py
    ├── requirements.txt
    ├── .env.example
    ├── .env
    ├── .gitignore
    ├── README.md
    ├── LICENSE
    ├── bot/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── handlers/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── notes.py
    │   │   ├── reminders.py
    │   │   ├── templates.py
    │   │   ├── admin.py
    │   │   ├── ai_chat.py
    │   │   └── example_handler.py
    │   ├── keyboards/
    │   │   ├── __init__.py
    │   │   └── builders.py
    │   ├── middlewares/
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   └── logging_middleware.py
    │   ├── states/
    │   │   ├── __init__.py
    │   │   └── states.py
    │   └── filters/
    │       ├── __init__.py
    │       └── admin.py
    ├── database/
    │   ├── __init__.py
    │   ├── database.py
    │   └── repositories/
    │       ├── __init__.py
    │       ├── base.py
    │       ├── users.py
    │       ├── notes.py
    │       ├── reminders.py
    │       └── templates.py
    ├── services/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── scheduler.py
    │   ├── script_runner.py
    │   ├── file_manager.py
    │   ├── ollama_service.py
    │   └── example_service.py
    ├── utils/
    │   ├── __init__.py
    │   ├── timezone.py
    │   └── helpers.py
    ├── scripts/
    │   ├── example_script.sh
    │   └── system_info.py
    ├── storage/
    │   └── files/
    └── logs/

### Описание директорий

**bot/** — модуль Telegram бота с обработчиками команд, клавиатурами, middleware и фильтрами.

**database/** — работа с базой данных SQLite через асинхронные репозитории.

**services/** — бизнес-логика приложения: планировщик напоминаний, выполнение скриптов, работа с AI.

**utils/** — вспомогательные функции для работы с часовыми поясами и форматированием.

**scripts/** — директория для скриптов, доступных администраторам для выполнения.

**storage/files/** — директория для сохранения файлов пользователей.

**logs/** — директория для логов приложения.

## Расширение функционала

### Создание нового обработчика

Создайте файл bot/handlers/my_handler.py:

    from aiogram import Router, F
    from aiogram.types import Message
    from aiogram.filters import Command
    
    router = Router(name="my_handler")
    
    @router.message(Command("mycommand"))
    async def cmd_mycommand(message: Message):
        await message.answer("Привет!")

Зарегистрируйте обработчик в bot/handlers/__init__.py:

    from .my_handler import router as my_router
    
    def setup_routers(dp: Dispatcher):
        dp.include_router(my_router)
        # ... остальные роутеры

### Создание нового сервиса

Создайте файл services/my_service.py:

    from .base import BaseService
    from database.database import Database
    
    class MyService(BaseService):
        def __init__(self, db: Database):
            super().__init__(db)
        
        async def do_something(self, data: str) -> bool:
            # Бизнес-логика
            return True

### Добавление скрипта для выполнения

Создайте скрипт в директории scripts/:

Bash скрипт (scripts/my_script.sh):

    #!/bin/bash
    echo "Скрипт выполнен!"
    date

Python скрипт (scripts/my_script.py):

    #!/usr/bin/env python3
    print("Python скрипт выполнен!")

## Архитектура

    Telegram API
         │
         ▼
    ┌─────────────────────────────────────┐
    │            Aiogram Bot              │
    │  Middlewares → Handlers → Filters   │
    └─────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────┐
    │             Services                │
    │  Scheduler │ Scripts │ Ollama │ ... │
    └─────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────┐
    │            Repositories             │
    │  Users │ Notes │ Reminders │ ...    │
    └─────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────┐
    │          SQLite Database            │
    └─────────────────────────────────────┘

### Используемые паттерны

**Repository Pattern** — абстракция работы с данными, отделение логики доступа к БД от бизнес-логики.

**Service Layer** — инкапсуляция бизнес-логики в отдельные сервисы.

**Middleware** — сквозная функциональность: аутентификация, логирование.

**FSM (Finite State Machine)** — реализация многошаговых диалогов с пользователем.

### Таблицы базы данных

| Таблица | Описание |
|---------|----------|
| users | Пользователи и их настройки |
| notes | Заметки пользователей |
| reminders | Напоминания (личные и групповые) |
| templates | Шаблоны для заметок и напоминаний |
| action_logs | Логи действий пользователей |
| received_files | Информация о полученных файлах |

## Используемые библиотеки

| Библиотека | Версия | Описание | Лицензия |
|------------|--------|----------|----------|
| [aiogram](https://github.com/aiogram/aiogram) | 3.4+ | Асинхронный фреймворк для Telegram Bot API | [MIT](https://github.com/aiogram/aiogram/blob/dev-3.x/LICENSE) |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.19+ | Асинхронная работа с SQLite | [MIT](https://github.com/omnilib/aiosqlite/blob/main/LICENSE) |
| [aiohttp](https://github.com/aio-libs/aiohttp) | 3.9+ | Асинхронный HTTP клиент для работы с Ollama API | [Apache 2.0](https://github.com/aio-libs/aiohttp/blob/master/LICENSE.txt) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0+ | Загрузка переменных окружения из .env файла | [BSD-3-Clause](https://github.com/theskumar/python-dotenv/blob/main/LICENSE) |
| [pytz](https://github.com/stub42/pytz) | 2024.1+ | Работа с часовыми поясами | [MIT](https://github.com/stub42/pytz/blob/master/LICENSE.txt) |

### Системные компоненты

| Компонент | Описание | Лицензия |
|-----------|----------|----------|
| [Python](https://www.python.org/) | Язык программирования | [PSF License](https://docs.python.org/3/license.html) |
| [SQLite](https://www.sqlite.org/) | Встраиваемая реляционная база данных | [Public Domain](https://www.sqlite.org/copyright.html) |
| [Ollama](https://ollama.com/) | Платформа для локального запуска LLM | [MIT](https://github.com/ollama/ollama/blob/main/LICENSE) |

## Лицензия

Этот проект распространяется под лицензией MIT.

    MIT License
    
    Copyright (c) 2024
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

## Вклад в проект

1. Сделайте форк репозитория
2. Создайте ветку для новой функции: git checkout -b feature/amazing-feature
3. Зафиксируйте изменения: git commit -m 'Add amazing feature'
4. Отправьте изменения: git push origin feature/amazing-feature
5. Откройте Pull Request

## Благодарности

- [Aiogram](https://github.com/aiogram/aiogram) — современный асинхронный фреймворк для создания Telegram ботов
- [aiosqlite](https://github.com/omnilib/aiosqlite) — асинхронная обёртка для работы с SQLite
- [aiohttp](https://github.com/aio-libs/aiohttp) — асинхронный HTTP клиент и сервер
- [Ollama](https://ollama.com/) — платформа для локального запуска больших языковых моделей
- [pytz](https://github.com/stub42/pytz) — библиотека для точной работы с часовыми поясами
