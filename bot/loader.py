"""
Загрузчик компонентов бота.

Этот модуль предоставляет глобальный доступ к основным компонентам
для использования в других модулях при необходимости.
"""

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config

# Создание экземпляра бота
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создание диспетчера
dp = Dispatcher()