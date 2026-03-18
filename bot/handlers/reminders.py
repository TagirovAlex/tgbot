"""
Обработчики для работы с напоминаниями.
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.database import Database
from database.repositories import ReminderRepository, TemplateRepository
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


# ============================================================================
# КОМАНДЫ
# ============================================================================

@router.message(Command("reminders"))
async def cmd_reminders(message: Message):
    """Команда /reminders."""
    await message.answer(
        "⏰ <b>Напоминания</b>\n\nВыберите действие:",
        reply_markup=get_reminders_menu_keyboard()
    )


@router.message(Command("remind"))
async def cmd_remind(message: Message, state: FSMContext, user: User):
    """
    Быстрая команда для создания напоминания.
    Работает и в личке, и в группе.
    
    Использование: /remind <текст>
    """
    # Извлекаем текст после команды
    text = message.text.replace("/remind", "").strip()
    
    chat_id = message.chat.id
    is_group = message.chat.type in ("group", "supergroup")
    
    if text:
        # Если текст указан, сохраняем и переходим к выбору времени
        await state.update_data(
            chat_id=chat_id,
            is_group=is_group,
            title=text
        )
        await state.set_state(ReminderStates.waiting_for_datetime)
        
        group_note = "\n\n👥 <i>Напоминание будет отправлено в эту группу.</i>" if is_group else ""
        
        await message.answer(
            f"⏰ <b>Создание напоминания</b>\n\n"
            f"Текст: {text}\n\n"
            f"📅 Введите дату и время.\n"
            f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            f"Например: 25.12.2024 15:30\n\n"
            f"<i>Ваш часовой пояс: {user.timezone}</i>"
            f"{group_note}",
            reply_markup=get_cancel_keyboard()
        )
    else:
        # Если текст не указан, начинаем полный диалог
        await state.update_data(chat_id=chat_id, is_group=is_group)
        await state.set_state(ReminderStates.waiting_for_title)
        
        group_note = "\n\n👥 <i>Напоминание будет отправлено в эту группу.</i>" if is_group else ""
        
        await message.answer(
            f"⏰ <b>Создание напоминания</b>\n\n"
            f"Введите текст напоминания:"
            f"{group_note}",
            reply_markup=get_cancel_keyboard()
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


# ============================================================================
# СОЗДАНИЕ НАПОМИНАНИЯ
# ============================================================================

@router.callback_query(F.data == "reminder_create")
async def callback_reminder_create(callback: CallbackQuery, state: FSMContext):
    """Начало создания напоминания."""
    chat_id = callback.message.chat.id
    is_group = callback.message.chat.type in ("group", "supergroup")
    
    await state.update_data(chat_id=chat_id, is_group=is_group)
    await state.set_state(ReminderStates.waiting_for_title)
    
    group_note = "\n\n👥 <i>Напоминание будет отправлено в эту группу.</i>" if is_group else ""
    
    await callback.message.edit_text(
        f"⏰ <b>Создание напоминания</b>\n\n"
        f"Введите текст напоминания:"
        f"{group_note}",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "reminder_create_group")
async def callback_reminder_create_group(callback: CallbackQuery, state: FSMContext):
    """Создание напоминания для группы (выбор группы)."""
    # Показываем инструкцию
    await callback.message.edit_text(
        "👥 <b>Напоминание в группу</b>\n\n"
        "Чтобы создать напоминание для группы:\n\n"
        "1. Добавьте бота в нужную группу\n"
        "2. Дайте боту права на отправку сообщений\n"
        "3. В группе напишите команду:\n"
        "   <code>/remind текст напоминания</code>\n\n"
        "Или просто напишите /remind в группе и следуйте инструкциям.",
        reply_markup=get_reminders_menu_keyboard()
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
    
    data = await state.get_data()
    is_group = data.get("is_group", False)
    group_note = "\n\n👥 <i>Напоминание будет отправлено в группу.</i>" if is_group else ""
    
    await callback.message.edit_text(
        f"📅 Введите дату и время напоминания.\n\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>"
        f"{group_note}",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_content)
async def process_reminder_content(message: Message, state: FSMContext, user: User):
    """Обработка описания."""
    await state.update_data(content=message.text)
    await state.set_state(ReminderStates.waiting_for_datetime)
    
    data = await state.get_data()
    is_group = data.get("is_group", False)
    group_note = "\n\n👥 <i>Напоминание будет отправлено в группу.</i>" if is_group else ""
    
    await message.answer(
        f"📅 Введите дату и время напоминания.\n\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>"
        f"{group_note}",
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


@router.callback_query(F.data.startswith("interval:"))
async def process_interval_selection(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Обработка выбора интервала."""
    interval = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    current_state = await state.get_state()
    
    # Если редактируем существующее напоминание
    if "edit_reminder_id" in data:
        reminder_id = data["edit_reminder_id"]
        await state.clear()
        
        reminder_repo = ReminderRepository(db)
        await reminder_repo.update(reminder_id, repeat_interval=interval)
        
        interval_str = format_interval(interval)
        
        await callback.message.edit_text(
            f"✅ Интервал повтора обновлён!\n\n"
            f"🔄 Новый интервал: {interval_str}",
            reply_markup=get_reminder_actions_keyboard(reminder_id)
        )
        await callback.answer()
        return
    
    # Если создаём новое напоминание
    if "chat_id" in data and "title" in data and "remind_at" in data:
        await state.clear()
        
        reminder_repo = ReminderRepository(db)
        reminder_id = await reminder_repo.create(
            user_id=user.id,
            chat_id=data["chat_id"],
            title=data["title"],
            content=data.get("content"),
            remind_at=data["remind_at"],
            repeat_interval=interval,
            is_group=data.get("is_group", False)
        )
        
        remind_at_str = format_user_time(data["remind_at"], user.timezone)
        interval_str = format_interval(interval)
        is_group = data.get("is_group", False)
        
        type_text = "👥 Групповое напоминание" if is_group else "👤 Личное напоминание"
        
        await callback.message.edit_text(
            f"✅ Напоминание создано!\n\n"
            f"<b>{data['title']}</b>\n\n"
            f"📅 Время: {remind_at_str}\n"
            f"🔄 Повтор: {interval_str}\n"
            f"📍 Тип: {type_text}",
            reply_markup=get_reminder_actions_keyboard(reminder_id)
        )
        await callback.answer()
        return
    
    # Если ничего не подошло
    await state.clear()
    await callback.answer("Ошибка: данные не найдены. Начните заново.", show_alert=True)
    await callback.message.edit_text(
        "❌ Произошла ошибка. Попробуйте создать напоминание заново.",
        reply_markup=get_reminders_menu_keyboard()
    )


# ============================================================================
# СОЗДАНИЕ НАПОМИНАНИЯ ИЗ ШАБЛОНА
# ============================================================================

@router.callback_query(F.data == "reminder_from_template")
async def callback_reminder_from_template(callback: CallbackQuery, user: User, db: Database, state: FSMContext):
    """Выбор шаблона для создания напоминания."""
    template_repo = TemplateRepository(db)
    templates = await template_repo.get_user_templates(user.id, template_type="reminder")
    
    if not templates:
        await callback.message.edit_text(
            "⏰ <b>Создание из шаблона</b>\n\n"
            "У вас нет шаблонов для напоминаний.\n\n"
            "Сначала создайте шаблон в разделе 📋 Шаблоны.",
            reply_markup=get_reminders_menu_keyboard()
        )
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    
    for template in templates:
        builder.row(
            InlineKeyboardButton(
                text=f"📋 {template.name}",
                callback_data=f"use_reminder_template:{template.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="reminders_menu"))
    
    await callback.message.edit_text(
        "⏰ <b>Создание из шаблона</b>\n\n"
        "Выберите шаблон:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("use_reminder_template:"))
async def callback_use_reminder_template(callback: CallbackQuery, user: User, db: Database, state: FSMContext):
    """Применение шаблона для напоминания."""
    template_id = int(callback.data.split(":")[1])
    
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    
    if not template or template.user_id != user.id:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    
    # Применяем шаблон с подстановкой переменных
    now = datetime.now()
    variables = {
        "name": user.full_name or user.username or "Пользователь",
        "date": now.strftime("%d.%m.%Y"),
        "time": now.strftime("%H:%M"),
    }
    
    title, content = template.apply(**variables)
    
    # Сохраняем данные из шаблона
    chat_id = callback.message.chat.id
    is_group = callback.message.chat.type in ("group", "supergroup")
    
    await state.update_data(
        chat_id=chat_id,
        is_group=is_group,
        title=title or template.name,
        content=content if content else None,
        from_template=True
    )
    
    await state.set_state(ReminderStates.waiting_for_datetime)
    
    preview = f"<b>Заголовок:</b> {title or template.name}\n"
    if content:
        preview += f"<b>Содержимое:</b> {content[:100]}{'...' if len(content) > 100 else ''}\n"
    
    group_note = "\n👥 <i>Напоминание будет отправлено в группу.</i>" if is_group else ""
    
    await callback.message.edit_text(
        f"⏰ <b>Создание из шаблона</b>\n\n"
        f"{preview}\n"
        f"📅 Введите дату и время напоминания.\n\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>"
        f"{group_note}",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


# ============================================================================
# СПИСОК НАПОМИНАНИЙ
# ============================================================================

@router.callback_query(F.data == "reminders_list")
async def callback_reminders_list(callback: CallbackQuery, user: User, db: Database):
    """Список напоминаний."""
    reminder_repo = ReminderRepository(db)
    reminders = await reminder_repo.get_user_reminders(user.id, active_only=False, limit=15)
    
    if not reminders:
        await callback.message.edit_text(
            "⏰ <b>Ваши напоминания</b>\n\n"
            "У вас пока нет напоминаний.",
            reply_markup=get_reminders_menu_keyboard()
        )
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    for reminder in reminders:
        remind_at_str = format_user_time(reminder.remind_at, user.timezone, "%d.%m %H:%M")
        status_icon = "✅" if reminder.is_active else "⏸"
        group_icon = "👥" if reminder.is_group else ""
        text = f"{status_icon}{group_icon} {remind_at_str} - {truncate_text(reminder.title, 20)}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"reminder_view:{reminder.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="reminders_menu"))
    
    await callback.message.edit_text(
        f"⏰ <b>Ваши напоминания</b> ({len(reminders)})\n\n"
        "✅ - активные, ⏸ - неактивные, 👥 - групповые\n\n"
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
    
    # Кнопки действий
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"reminder_edit:{reminder.id}"
        ),
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"reminder_delete:{reminder.id}"
        )
    )
    
    if reminder.is_active:
        builder.row(
            InlineKeyboardButton(
                text="⏸ Приостановить",
                callback_data=f"reminder_deactivate:{reminder.id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="▶️ Активировать",
                callback_data=f"reminder_activate:{reminder.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="reminders_list"))
    
    await callback.message.edit_text(
        f"⏰ <b>{reminder.title}</b>\n\n"
        f"{content}\n\n"
        f"📅 Время: {remind_at_str}\n"
        f"🔄 Повтор: {interval_str}\n"
        f"📍 Тип: {reminder_type}\n"
        f"📊 Статус: {status}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ============================================================================
# РЕДАКТИРОВАНИЕ НАПОМИНАНИЯ
# ============================================================================

@router.callback_query(F.data.startswith("reminder_edit:"))
async def callback_reminder_edit(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Меню редактирования напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить текст",
            callback_data=f"reminder_edit_title:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📄 Изменить описание",
            callback_data=f"reminder_edit_content:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📅 Изменить время",
            callback_data=f"reminder_edit_time:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Изменить повтор",
            callback_data=f"reminder_edit_interval:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"reminder_view:{reminder_id}")
    )
    
    content_preview = reminder.content[:50] + "..." if reminder.content and len(reminder.content) > 50 else (reminder.content or "(нет описания)")
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование</b>\n\n"
        f"<b>Текст:</b> {reminder.title}\n"
        f"<b>Описание:</b> {content_preview}\n\n"
        f"Что вы хотите изменить?",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_edit_title:"))
async def callback_reminder_edit_title(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Редактирование текста напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await state.update_data(edit_reminder_id=reminder_id)
    await state.set_state(ReminderStates.waiting_for_edit_title)
    
    await callback.message.edit_text(
        f"📝 <b>Редактирование текста</b>\n\n"
        f"Текущий текст:\n<i>{reminder.title}</i>\n\n"
        f"Введите новый текст напоминания:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_edit_title)
async def process_reminder_edit_title(message: Message, state: FSMContext, db: Database):
    """Обработка нового текста напоминания."""
    data = await state.get_data()
    reminder_id = data["edit_reminder_id"]
    await state.clear()
    
    reminder_repo = ReminderRepository(db)
    await reminder_repo.update(reminder_id, title=message.text)
    
    await message.answer(
        f"✅ Текст напоминания обновлён!\n\n"
        f"Новый текст: <b>{message.text}</b>",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )


@router.callback_query(F.data.startswith("reminder_edit_content:"))
async def callback_reminder_edit_content(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Редактирование описания напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await state.update_data(edit_reminder_id=reminder_id)
    await state.set_state(ReminderStates.waiting_for_edit_content)
    
    current_content = reminder.content or "(нет описания)"
    
    # Кнопки с возможностью удалить описание
    builder = InlineKeyboardBuilder()
    if reminder.content:
        builder.row(
            InlineKeyboardButton(
                text="🗑 Удалить описание",
                callback_data=f"reminder_clear_content:{reminder_id}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"reminder_edit:{reminder_id}")
    )
    
    await callback.message.edit_text(
        f"📄 <b>Редактирование описания</b>\n\n"
        f"Текущее описание:\n<i>{current_content}</i>\n\n"
        f"Введите новое описание или выберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_edit_content)
async def process_reminder_edit_content(message: Message, state: FSMContext, db: Database):
    """Обработка нового описания напоминания."""
    data = await state.get_data()
    reminder_id = data["edit_reminder_id"]
    await state.clear()
    
    reminder_repo = ReminderRepository(db)
    await reminder_repo.update(reminder_id, content=message.text)
    
    await message.answer(
        f"✅ Описание обновлено!\n\n"
        f"Новое описание:\n<i>{message.text}</i>",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )


@router.callback_query(F.data.startswith("reminder_clear_content:"))
async def callback_reminder_clear_content(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Удаление описания напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    # Очищаем состояние если было
    await state.clear()
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    # Устанавливаем content = None (пустое описание)
    await reminder_repo.update(reminder_id, content=None)
    
    await callback.answer("✅ Описание удалено", show_alert=True)
    
    await callback.message.edit_text(
        f"✅ Описание удалено!\n\n"
        f"Напоминание: <b>{reminder.title}</b>",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )


@router.callback_query(F.data.startswith("reminder_edit_time:"))
async def callback_reminder_edit_time(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Редактирование времени напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await state.update_data(edit_reminder_id=reminder_id)
    await state.set_state(ReminderStates.waiting_for_edit_datetime)
    
    current_time = format_user_time(reminder.remind_at, user.timezone)
    
    await callback.message.edit_text(
        f"📅 <b>Редактирование времени</b>\n\n"
        f"Текущее время: <b>{current_time}</b>\n\n"
        f"Введите новую дату и время.\n"
        f"Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        f"Например: 25.12.2024 15:30\n\n"
        f"<i>Ваш часовой пояс: {user.timezone}</i>",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_edit_datetime)
async def process_reminder_edit_datetime(message: Message, state: FSMContext, user: User, db: Database):
    """Обработка нового времени напоминания."""
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
            "❌ Нельзя установить время в прошлом.\n"
            "Введите корректную дату и время:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    reminder_id = data["edit_reminder_id"]
    await state.clear()
    
    reminder_repo = ReminderRepository(db)
    # При изменении времени также активируем напоминание
    await reminder_repo.update(reminder_id, remind_at=remind_at, is_active=1)
    
    remind_at_str = format_user_time(remind_at, user.timezone)
    
    await message.answer(
        f"✅ Время обновлено!\n\n"
        f"📅 Новое время: <b>{remind_at_str}</b>\n\n"
        f"<i>Напоминание активировано.</i>",
        reply_markup=get_reminder_actions_keyboard(reminder_id)
    )


@router.callback_query(F.data.startswith("reminder_edit_interval:"))
async def callback_reminder_edit_interval(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Редактирование интервала повтора."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    await state.update_data(edit_reminder_id=reminder_id)
    await state.set_state(ReminderStates.waiting_for_repeat_interval)
    
    current_interval = format_interval(reminder.repeat_interval)
    
    await callback.message.edit_text(
        f"🔄 <b>Редактирование повтора</b>\n\n"
        f"Текущий интервал: <b>{current_interval}</b>\n\n"
        f"Выберите новый интервал повтора:",
        reply_markup=get_repeat_interval_keyboard()
    )
    await callback.answer()
# ============================================================================
# УДАЛЕНИЕ / АКТИВАЦИЯ / ДЕАКТИВАЦИЯ
# ============================================================================

@router.callback_query(F.data.startswith("reminder_delete:"))
async def callback_reminder_delete(callback: CallbackQuery):
    """Подтверждение удаления."""
    reminder_id = int(callback.data.split(":")[1])
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"reminder_delete_confirm:{reminder_id}"
        ),
        InlineKeyboardButton(
            text="❌ Нет",
            callback_data=f"reminder_view:{reminder_id}"
        )
    )
    
    await callback.message.edit_text(
        "🗑 <b>Удаление напоминания</b>\n\n"
        "Вы уверены, что хотите удалить это напоминание?",
        reply_markup=builder.as_markup()
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
    
    await callback.answer("⏸ Напоминание приостановлено", show_alert=True)
    
    # Обновляем отображение
    await callback_reminder_view(callback, user, db)


@router.callback_query(F.data.startswith("reminder_activate:"))
async def callback_reminder_activate(callback: CallbackQuery, user: User, db: Database):
    """Активация напоминания."""
    reminder_id = int(callback.data.split(":")[1])
    
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id)
    
    if not reminder or reminder.user_id != user.id:
        await callback.answer("Напоминание не найдено", show_alert=True)
        return
    
    # Проверяем, не в прошлом ли время напоминания
    from utils.timezone import ensure_datetime
    remind_at = ensure_datetime(reminder.remind_at)
    
    if remind_at and remind_at < datetime.utcnow():
        await callback.answer(
            "❌ Время напоминания в прошлом. Сначала измените время.",
            show_alert=True
        )
        return
    
    await reminder_repo.update(reminder_id, is_active=1)
    
    await callback.answer("✅ Напоминание активировано", show_alert=True)
    
    # Обновляем отображение
    await callback_reminder_view(callback, user, db)