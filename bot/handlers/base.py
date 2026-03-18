"""
Базовые обработчики: start, help, главное меню.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database.repositories.users import User
from bot.keyboards.builders import (
    get_main_menu_keyboard,
    get_admin_menu_keyboard,
)
from bot.filters import IsAdminFilter

router = Router(name="base")


@router.message(CommandStart())
async def cmd_start(message: Message, user: User):
    """Команда /start."""
    await message.answer(
        f"👋 Привет, <b>{user.full_name or user.username or 'друг'}</b>!\n\n"
        "Я бот-ассистент для управления заметками и напоминаниями.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help."""
    help_text = """
<b>📚 Справка по командам</b>

<b>Основные команды:</b>
/start - Главное меню
/help - Эта справка
/notes - Управление заметками
/reminders - Управление напоминаниями
/templates - Управление шаблонами
/timezone - Настройка часового пояса

<b>Команды администратора:</b>
/admin - Панель администратора
/users - Список пользователей
/scripts - Выполнение скриптов
/restart - Перезапуск бота

<b>Работа с шаблонами:</b>
В шаблонах можно использовать переменные:
{{name}} - имя пользователя
{{date}} - текущая дата
{{time}} - текущее время

<b>Формат даты для напоминаний:</b>
ДД.ММ.ГГГГ ЧЧ:ММ (например: 25.12.2024 15:30)
"""
    await message.answer(help_text)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Справка через callback."""
    await callback.message.edit_text(
        "📚 <b>Справка</b>\n\n"
        "Используйте команду /help для получения полной справки.\n\n"
        "Или выберите раздел в меню для начала работы.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n"
        "🏠 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Пустой callback для информационных кнопок."""
    await callback.answer()


# === Админ меню ===

@router.message(Command("admin"), IsAdminFilter())
async def cmd_admin(message: Message):
    """Команда /admin - панель администратора."""
    await message.answer(
        "🔐 <b>Панель администратора</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )


@router.callback_query(F.data == "admin_menu", IsAdminFilter())
async def callback_admin_menu(callback: CallbackQuery):
    """Меню администратора."""
    await callback.message.edit_text(
        "🔐 <b>Панель администратора</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()