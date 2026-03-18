# Telegram Assistant Bot

Многофункциональный Telegram-бот для управления заметками, напоминаниями и выполнения административных задач.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)
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

- **Заметки** — создание, редактирование, удаление, просмотр списка заметок
- **Напоминания** — личные и групповые напоминания с поддержкой повторения (ежечасно, ежедневно, еженедельно, ежемесячно)
- **Шаблоны** — создание шаблонов для быстрого создания заметок и напоминаний с поддержкой переменных
- **Часовые пояса** — автоматический учёт часового пояса пользователя при создании напоминаний

### Для администраторов

- **Управление пользователями** — просмотр списка, назначение и снятие прав администратора
- **Выполнение скриптов** — запуск bash и python скриптов на сервере через меню бота
- **Логи действий** — просмотр истории действий всех пользователей
- **Перезапуск бота** — удалённый перезапуск через команду или меню
- **Управление файлами** — автоматическое сохранение полученных файлов с разбивкой по пользователям

## Требования

- Python 3.10 или выше
- pip (менеджер пакетов Python)
- SQLite 3 (встроен в Python)

## Установка

Клонируйте репозиторий:

    git clone https://github.com/yourusername/telegram-assistant-bot.git
    cd telegram-assistant-bot

Создайте виртуальное окружение:

    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows

Установите зависимости:

    pip install -r requirements.txt

Создайте файл конфигурации:

    cp .env.example .env
    nano .env

## Конфигурация

Отредактируйте файл .env:

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

## Запуск

### Локальный запуск

    source venv/bin/activate
    python main.py

### Запуск как systemd сервис (Linux)

Создайте файл /etc/systemd/system/telegram-bot.service:

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

Запустите сервис:

    sudo systemctl daemon-reload
    sudo systemctl enable telegram-bot
    sudo systemctl start telegram-bot
    sudo systemctl status telegram-bot

## Использование

### Основные команды

| Команда | Описание |
|---------|----------|
| /start | Главное меню |
| /help | Справка по командам |
| /notes | Управление заметками |
| /reminders | Управление напоминаниями |
| /remind [текст] | Быстрое создание напоминания |
| /templates | Управление шаблонами |
| /timezone | Настройка часового пояса |

### Команды администратора

| Команда | Описание |
|---------|----------|
| /admin | Панель администратора |
| /users | Список пользователей |
| /scripts | Список доступных скриптов |
| /logs | Последние действия пользователей |
| /restart | Перезапуск бота |

### Создание напоминания в группе

1. Добавьте бота в группу
2. Дайте боту права на отправку сообщений
3. Напишите в группе: /remind Текст напоминания
4. Укажите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ
5. Выберите интервал повтора

### Использование шаблонов

Шаблоны поддерживают переменные:

| Переменная | Описание |
|------------|----------|
| {{name}} | Имя пользователя |
| {{date}} | Текущая дата (ДД.ММ.ГГГГ) |
| {{time}} | Текущее время (ЧЧ:ММ) |

Пример шаблона: Заметка от {{date}} - {{name}}

## Структура проекта

    telegram-assistant-bot/
    ├── main.py                      # Точка входа
    ├── config.py                    # Конфигурация
    ├── requirements.txt             # Зависимости Python
    ├── .env.example                 # Пример конфигурации
    ├── .gitignore                   # Игнорируемые файлы
    ├── README.md                    # Документация
    ├── LICENSE                      # Лицензия MIT
    ├── bot/
    │   ├── __init__.py
    │   ├── loader.py                # Загрузчик компонентов
    │   ├── handlers/
    │   │   ├── __init__.py          # Регистрация роутеров
    │   │   ├── base.py              # Базовые команды
    │   │   ├── notes.py             # Работа с заметками
    │   │   ├── reminders.py         # Работа с напоминаниями
    │   │   ├── templates.py         # Работа с шаблонами
    │   │   ├── admin.py             # Административные функции
    │   │   └── example_handler.py   # Пример обработчика
    │   ├── keyboards/
    │   │   ├── __init__.py
    │   │   └── builders.py          # Построители клавиатур
    │   ├── middlewares/
    │   │   ├── __init__.py
    │   │   ├── auth.py              # Аутентификация
    │   │   └── logging_middleware.py
    │   ├── states/
    │   │   ├── __init__.py
    │   │   └── states.py            # FSM состояния
    │   └── filters/
    │       ├── __init__.py
    │       └── admin.py             # Фильтр администратора
    ├── database/
    │   ├── __init__.py
    │   ├── database.py              # Менеджер SQLite
    │   └── repositories/
    │       ├── __init__.py
    │       ├── base.py              # Базовый репозиторий
    │       ├── users.py             # Пользователи
    │       ├── notes.py             # Заметки
    │       ├── reminders.py         # Напоминания
    │       └── templates.py         # Шаблоны
    ├── services/
    │   ├── __init__.py
    │   ├── base.py                  # Базовый сервис
    │   ├── scheduler.py             # Планировщик напоминаний
    │   ├── script_runner.py         # Выполнение скриптов
    │   ├── file_manager.py          # Управление файлами
    │   └── example_service.py       # Пример сервиса
    ├── utils/
    │   ├── __init__.py
    │   ├── timezone.py              # Работа с часовыми поясами
    │   └── helpers.py               # Вспомогательные функции
    ├── scripts/
    │   ├── example_script.sh
    │   └── system_info.py
    ├── storage/files/
    └── logs/

## Расширение функционала

### Создание нового обработчика

Создайте файл bot/handlers/my_handler.py:

    from aiogram import Router, F
    from aiogram.types import Message
    from aiogram.filters import Command

    router = Router(name="my_handler")

    @router.message(Command("mycommand"))
    async def cmd_mycommand(message: Message):
        """Обработчик команды /mycommand."""
        await message.answer("Привет!")

Зарегистрируйте в bot/handlers/__init__.py:

    from .my_handler import router as my_router

    def setup_routers(dp: Dispatcher):
        dp.include_router(my_router)

### Создание нового сервиса

Создайте файл services/my_service.py:

    from .base import BaseService
    from database.database import Database

    class MyService(BaseService):
        def __init__(self, db: Database):
            super().__init__(db)
        
        async def do_something(self, data: str) -> bool:
            return True

### Добавление скрипта

Положите скрипт в папку scripts/:

    #!/bin/bash
    # scripts/my_script.sh
    echo "Скрипт выполнен!"

## Архитектура

    ┌─────────────────────────────────────────────────────────┐
    │                     Telegram API                         │
    └─────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │                    Aiogram Bot                           │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
    │  │ Middlewares │──│  Handlers   │──│   Filters   │      │
    │  └─────────────┘  └─────────────┘  └─────────────┘      │
    └─────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │                      Services                            │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
    │  │Scheduler │  │ Scripts  │  │  Files   │               │
    │  └──────────┘  └──────────┘  └──────────┘               │
    └─────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │                    Repositories                          │
    │  ┌───────┐  ┌───────┐  ┌───────────┐  ┌──────────┐     │
    │  │ Users │  │ Notes │  │ Reminders │  │Templates │     │
    │  └───────┘  └───────┘  └───────────┘  └──────────┘     │
    └─────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │                   SQLite Database                        │
    └─────────────────────────────────────────────────────────┘

### Паттерны проектирования

- **Repository Pattern** — абстракция работы с данными
- **Service Layer** — инкапсуляция бизнес-логики
- **Middleware** — сквозная функциональность
- **FSM (Finite State Machine)** — многошаговые диалоги

### Таблицы базы данных

| Таблица | Описание |
|---------|----------|
| users | Пользователи и их настройки |
| notes | Заметки пользователей |
| reminders | Напоминания |
| templates | Шаблоны |
| action_logs | Логи действий |
| received_files | Информация о файлах |

## Используемые библиотеки

| Библиотека | Версия | Описание | Лицензия |
|------------|--------|----------|----------|
| [aiogram](https://github.com/aiogram/aiogram) | 3.4+ | Асинхронный фреймворк для Telegram Bot API | [MIT](https://github.com/aiogram/aiogram/blob/dev-3.x/LICENSE) |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.19+ | Асинхронная работа с SQLite | [MIT](https://github.com/omnilib/aiosqlite/blob/main/LICENSE) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0+ | Загрузка переменных окружения из .env | [BSD-3-Clause](https://github.com/theskumar/python-dotenv/blob/main/LICENSE) |
| [pytz](https://pythonhosted.org/pytz/) | 2024.1+ | Работа с часовыми поясами | [MIT](https://github.com/stub42/pytz/blob/master/LICENSE.txt) |

### Системные компоненты

| Компонент | Описание | Лицензия |
|-----------|----------|----------|
| [Python](https://www.python.org/) | Язык программирования | [PSF License](https://docs.python.org/3/license.html) |
| [SQLite](https://www.sqlite.org/) | Встраиваемая база данных | [Public Domain](https://www.sqlite.org/copyright.html) |
| [asyncio](https://docs.python.org/3/library/asyncio.html) | Асинхронное программирование | [PSF License](https://docs.python.org/3/license.html) |

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

1. Форкните репозиторий
2. Создайте ветку (git checkout -b feature/amazing-feature)
3. Зафиксируйте изменения (git commit -m 'Add amazing feature')
4. Отправьте в ветку (git push origin feature/amazing-feature)
5. Откройте Pull Request

## Благодарности

- [Aiogram](https://github.com/aiogram/aiogram) — современный асинхронный фреймворк для Telegram Bot API
- [aiosqlite](https://github.com/omnilib/aiosqlite) — асинхронная обёртка для SQLite
- [pytz](https://pythonhosted.org/pytz/) — точная работа с часовыми поясами
