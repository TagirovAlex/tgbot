"""
Обработчики для работы с напоминаниями.
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.database import Database
from database.repositories import ReminderRepository
from database.repositories.users import User
from bot.states import ReminderStates
from bot.keyboards.builders import (
    get_reminders_menu_keyboard,
    get_reminder_actions_keyboard,
    get_repeat_interval_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
)
from utils.timezone import parse_user_datetime, format_user_time
from utils.helpers import format_interval, truncate_text

router = Router(name="reminders")


@router.message(Command("reminders"))
async def cmd_reminders(message: Message):
    """Команда /reminders."""
    await message.answer(
        "⏰ <b>Напоминания</b>\n\nВыберите действие:",
        reply_markup=get_reminders_menu_keyboard()
    )


@router.callback_query(F.data == "reminders_menu")
async def callback_reminders_menu(callback: CallbackQuery, state: FSMContext):
    """Меню напоминаний."""
    await state.clear()
    await callback.message.edit_text(
        "⏰ <b>Напоминания</b>\n\nВыберите действие:",
        reply_markup=get_reminders_menu_keyboard()
    )
    await callback.answer()


# === Создание напоминания ===

@router.callback_query(F.data == "reminder_create")
async def callback_reminder_create(callback: CallbackQuery, state: FSMContext):
    """Начало создания напоминания."""
    # Сохраняем chat_id для определения личное/групповое
    chat_id = callback.message.chat.id
    is_group = callback.message.chat.type in ("group", "supergroup")
    
    await state.update_data(chat_id=chat_id, is_group=is_group)
    await state.set_state(ReminderStates.waiting_for_title)
    
    await callback.message.edit_text(
        "⏰ <b>Создание напоминания</b>\n\n"
        "Введите текст напоминания:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_title)
async def process_reminder_title(message: Message, state: FSMContext):
    """Обработка текста напоминания."""
    await state.update_data(title=message.text)
    await state.set_state(ReminderStates.waiting_for_content)
    
    await message.answer(
        "Введите дополнительное описание или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard("skip_reminder_content")
    )


@router.callback_query(F.data == "skip_reminder_content", ReminderStates.waiting_for_content)
async def skip_reminder_content(callback: CallbackQuery, state: FSMContext, user: User):
    """Пропуск описания."""
    await state.set_state(ReminderStates.waiting_for_datetime)
    await callback.message.edit_text(
        f"📅 Введите дату и время напоминания.\n\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_content)
async def process_reminder_content(message: Message, state: FSMContext, user: User):
    """Обработка описания."""
    await state.update_data(content=message.text)
    await state.set_state(ReminderStates.waiting_for_datetime)
    
    await message.answer(
        f"📅 Введите дату и время напоминания.\n\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ReminderStates.waiting_for_datetime)
async def process_reminder_datetime(message: Message, state: FSMContext, user: User):
    """Обработка даты и времени."""
    remind_at = parse_user_datetime(message.text, user.timezone)
    
    if not remind_at:
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 25.12.2024 15:30",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if remind_at < datetime.utcnow():
        await message.answer(
            "❌ Нельзя создать напоминание в прошлом.\n"
            "Введите корректную дату и время:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(remind_at=remind_at)
    await state.set_state(ReminderStates.waiting_for_repeat_interval)
    
    await message.answer(
        "🔄 Выберите интервал повтора:",
        reply_markup=get_repeat_interval_keyboard()
    )


@router.callback_query(F.data.startswith("interval:"), ReminderStates.waiting_for_repeat_interval)
async def process_reminder_interval(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Обработка выбора интервала."""
    interval = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    await state.clear()
    
    reminder_repo = ReminderRepository(db)
    reminder_id = await reminder_repo.create(
        user_id=user.id,
        chat_id=data["chat_id"],
        title=data["title"],
        content=data.get("content"),
        remind_at=data["remind_at"],
        repeat_interval=interval,
        is_group=data["is_group"]
    )
    
    remind_at_str = format_user_time(data["remind_at"], user.timezone)
    interval_str = format_interval(interval)
    
    await callback.message.edit_text(
        f"✅ Напоминание создано!\n\n"
        f"<b>{data['title']}</b>\n"
        f"📅 {remind_at_str}\n"
        f"🔄 {interval_str}",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )
    await callback.answer()


# === Список напоминаний ===

@router.callback_query(F.data == "reminders_list")
async def callback_reminders_list(callback: CallbackQuery, user: User, db: Database):
    """Список напоминаний."""
    reminder_repo = ReminderRepository(db)
    reminders = await reminder_repo.get_user_reminders(user.id, limit=10)
    
    if not reminders:
        await callback.message.edit_text(
            "⏰ <b>Ваши напоминания</b>\n\n"
            "У вас пока нет активных напоминаний.",
            reply_markup=get_reminders_menu_keyboard()
        )
        await callback.answer()
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    for reminder in reminders:
        remind_at_str = format_user_time(reminder.remind_at, user.timezone, "%d.%m %H:%M")
        text = f"⏰ {remind_at_str} - {truncate_text(reminder.title, 25)}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"reminder_view:{reminder.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="reminders_menu"))
    
    await callback.message.edit_text(
        f"⏰ <b>Ваши напоминания</b> ({len(reminders)})\n\n"
        "Выберите напоминание:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_view:"))
async def callback_reminder_view(callback: CallbackQuery, user: User, db: Database):
    """Просмотр напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    remind_at_str = format_user_time(reminder.remind_at, user.timezone)
    interval_str = format_interval(reminder.repeat_interval)
    status = "✅ Активно" if reminder.is_active else "⏸ Неактивно"
    reminder_type = "👥 Групповое" if reminder.is_group else "👤 Личное"
    
    content = reminder.content or "(без описания)"
    
    await callback.message.edit_text(
        f"⏰ <b>{reminder.title}</b>\n\n"
        f"{content}\n\n"
        f"📅 Время: {remind_at_str}\n"
        f"🔄 Повтор: {interval_str}\n"
        f"📍 Тип: {reminder_type}\n"
        f"📊 Статус: {status}",
        reply_markup=get_reminder_actions_keyboard(reminder.id)
    )
    await callback.answer()


# === Удаление напоминания ===

@router.callback_query(F.data.startswith("reminder_delete:"))
async def callback_reminder_delete(callback: CallbackQuery):
    """Подтверждение удаления."""
    reminder_id = int(callback.data.split(":")[1])
    
    from bot.keyboards.builders import get_confirmation_keyboard
    
    await callback.message.edit_text(
        "🗑 <b>Удаление напоминания</b>\n\n"
        "Вы уверены?",
        reply_markup=get_confirmation_keyboard("reminder_delete", reminder_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_delete_confirm:"))
async def callback_reminder_delete_confirm(callback: CallbackQuery, user: User, db: Database):
    """Подтверждение удаления."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await reminder_repo.delete(reminder_id)
    
    await callback.message.edit_text(
        "✅ Напоминание удалено!",
        reply_markup=get_reminders_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_delete_cancel:"))
async def callback_reminder_delete_cancel(callback: CallbackQuery):
    """Отмена удаления."""
    reminder_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "❌ Удаление отменено.",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )
    await callback.answer()


# === Деактивация напоминания ===

@router.callback_query(F.data.startswith("reminder_deactivate:"))
async def callback_reminder_deactivate(callback: CallbackQuery, user: User, db: Database):
    """Деактивация напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await reminder_repo.deactivate(reminder_id)
    
    await callback.message.edit_text(
        "⏸ Напоминание деактивировано!",
        reply_markup=get_reminders_menu_keyboard()
    )
    await callback.answer()