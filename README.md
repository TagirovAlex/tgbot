# tgbot
README.md

# 🤖 Telegram Bot
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Многофункциональный Telegram-бот для управления заметками, напоминаниями и выполнения административных задач.

Бот создавался в качестве небольшой проверки "вайбкодинга", может содержать ошибки, недочеты и много всего другого.
Использование исключительно на свой страх и риск.


## Возможности

### Для всех пользователей
- 📝 **Заметки**: создание, редактирование, удаление, просмотр списка
- ⏰ **Напоминания**: личные и групповые, с поддержкой повторения
- 📋 **Шаблоны**: создание шаблонов для заметок и напоминаний
- 🌍 **Часовые пояса**: автоматический учёт часового пояса пользователя

### Для администраторов
- 🔄 Перезапуск бота
- 📂 Просмотр и выполнение скриптов на сервере
- 👥 Управление правами пользователей
- 📊 Просмотр логов

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/telegram-assistant-bot.git
cd telegram-assistant-bot

2. Создание виртуального окружения

Bash

python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows

3. Установка зависимостей

Bash

pip install -r requirements.txt

4. Настройка переменных окружения

Bash

cp .env.example .env
# Отредактируйте .env файл

5. Запуск

Bash

python main.py

Конфигурация

Отредактируйте файл .env:

env

BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_PATH=database.db
SCRIPTS_DIR=scripts
FILES_DIR=storage/files
LOGS_DIR=logs
SERVER_TIMEZONE=UTC

Структура базы данных

    users - пользователи и их права
    notes - заметки пользователей
    reminders - напоминания
    templates - шаблоны для заметок и напоминаний
    action_logs - логи действий

Расширение функционала

Смотрите документацию в файлах:

    bot/handlers/example_handler.py - пример создания обработчика
    services/example_service.py - пример создания сервиса

Команды бота
Основные команды

    /start - Начало работы
    /help - Справка
    /notes - Управление заметками
    /reminders - Управление напоминаниями
    /templates - Управление шаблонами
    /timezone - Настройка часового пояса

Команды администратора

    /admin - Панель администратора
    /users - Управление пользователями
    /scripts - Выполнение скриптов
    /restart - Перезапуск бота
    /logs - Просмотр логов

Лицензия
MIT License

Copyright (c) 2024 Your Name

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
MIT License
