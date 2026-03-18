"""
Обработчики для работы с заметками.
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.database import Database
from database.repositories import NoteRepository, TemplateRepository
from database.repositories.users import User
from bot.states import NoteStates
from bot.keyboards.builders import (
    get_notes_menu_keyboard,
    get_note_actions_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_main_menu_keyboard,
)
from utils.helpers import truncate_text

router = Router(name="notes")


@router.message(Command("notes"))
async def cmd_notes(message: Message):
    """Команда /notes."""
    await message.answer(
        "📝 <b>Заметки</b>\n\nВыберите действие:",
        reply_markup=get_notes_menu_keyboard()
    )


@router.callback_query(F.data == "notes_menu")
async def callback_notes_menu(callback: CallbackQuery, state: FSMContext):
    """Меню заметок."""
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Заметки</b>\n\nВыберите действие:",
        reply_markup=get_notes_menu_keyboard()
    )
    await callback.answer()


# ============================================================================
# СОЗДАНИЕ ЗАМЕТКИ
# ============================================================================

@router.callback_query(F.data == "note_create")
async def callback_note_create(callback: CallbackQuery, state: FSMContext):
    """Начало создания заметки."""
    await state.set_state(NoteStates.waiting_for_title)
    await callback.message.edit_text(
        "📝 <b>Создание заметки</b>\n\n"
        "Введите заголовок заметки:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(NoteStates.waiting_for_title)
async def process_note_title(message: Message, state: FSMContext):
    """Обработка заголовка заметки."""
    await state.update_data(title=message.text)
    await state.set_state(NoteStates.waiting_for_content)
    
    await message.answer(
        "Введите содержимое заметки или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard("skip_content")
    )


@router.callback_query(F.data == "skip_content", NoteStates.waiting_for_content)
async def skip_note_content(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Пропуск содержимого заметки."""
    await _save_note(callback.message, state, user, db, content=None, edit_message=True)
    await callback.answer()


@router.message(NoteStates.waiting_for_content)
async def process_note_content(message: Message, state: FSMContext, user: User, db: Database):
    """Обработка содержимого заметки."""
    await _save_note(message, state, user, db, content=message.text, edit_message=False)


async def _save_note(message: Message, state: FSMContext, user: User, db: Database, content: str = None, edit_message: bool = False):
    """Сохранение заметки."""
    data = await state.get_data()
    await state.clear()
    
    note_repo = NoteRepository(db)
    note_id = await note_repo.create(
        user_id=user.id,
        title=data["title"],
        content=content
    )
    
    text = (
        f"✅ Заметка создана!\n\n"
        f"<b>{data['title']}</b>\n"
        f"{content or '(без содержимого)'}"
    )
    
    if edit_message:
        await message.edit_text(text, reply_markup=get_note_actions_keyboard(note_id))
    else:
        await message.answer(text, reply_markup=get_note_actions_keyboard(note_id))


# ============================================================================
# СОЗДАНИЕ ЗАМЕТКИ ИЗ ШАБЛОНА
# ============================================================================

@router.callback_query(F.data == "note_from_template")
async def callback_note_from_template(callback: CallbackQuery, user: User, db: Database, state: FSMContext):
    """Выбор шаблона для создания заметки."""
    template_repo = TemplateRepository(db)
    templates = await template_repo.get_user_templates(user.id, template_type="note")
    
    if not templates:
        await callback.message.edit_text(
            "📝 <b>Создание из шаблона</b>\n\n"
            "У вас нет шаблонов для заметок.\n\n"
            "Сначала создайте шаблон в разделе 📋 Шаблоны.",
            reply_markup=get_notes_menu_keyboard()
        )
        await callback.answer()
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    for template in templates:
        builder.row(
            InlineKeyboardButton(
                text=f"📋 {template.name}",
                callback_data=f"use_note_template:{template.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="notes_menu"))
    
    await callback.message.edit_text(
        "📝 <b>Создание из шаблона</b>\n\n"
        "Выберите шаблон:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("use_note_template:"))
async def callback_use_note_template(callback: CallbackQuery, user: User, db: Database, state: FSMContext):
    """Применение шаблона для заметки."""
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
    
    # Создаём заметку сразу
    note_repo = NoteRepository(db)
    note_id = await note_repo.create(
        user_id=user.id,
        title=title or template.name,
        content=content if content else None
    )
    
    await callback.message.edit_text(
        f"✅ Заметка создана из шаблона!\n\n"
        f"<b>{title or template.name}</b>\n"
        f"{content or '(без содержимого)'}",
        reply_markup=get_note_actions_keyboard(note_id)
    )
    await callback.answer()


# ============================================================================
# СПИСОК ЗАМЕТОК
# ============================================================================

@router.callback_query(F.data == "notes_list")
async def callback_notes_list(callback: CallbackQuery, user: User, db: Database):
    """Список заметок пользователя."""
    note_repo = NoteRepository(db)
    notes = await note_repo.get_user_notes(user.id, limit=10)
    
    if not notes:
        await callback.message.edit_text(
            "📝 <b>Ваши заметки</b>\n\n"
            "У вас пока нет заметок.",
            reply_markup=get_notes_menu_keyboard()
        )
        await callback.answer()
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    for note in notes:
        builder.row(
            InlineKeyboardButton(
                text=truncate_text(note.title, 40),
                callback_data=f"note_view:{note.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="notes_menu"))
    
    await callback.message.edit_text(
        f"📝 <b>Ваши заметки</b> ({len(notes)})\n\n"
        "Выберите заметку для просмотра:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("note_view:"))
async def callback_note_view(callback: CallbackQuery, user: User, db: Database):
    """Просмотр заметки."""
    note_id = int(callback.data.split(":")[1])
    
    note_repo = NoteRepository(db)
    note = await note_repo.get_by_id(note_id)
    
    if not note or note.user_id != user.id:
        await callback.answer("Заметка не найдена", show_alert=True)
        return
    
    content = note.content or "(без содержимого)"
    
    await callback.message.edit_text(
        f"📝 <b>{note.title}</b>\n\n"
        f"{content}\n\n"
        f"<i>Создано: {note.created_at}</i>",
        reply_markup=get_note_actions_keyboard(note.id)
    )
    await callback.answer()


# ============================================================================
# РЕДАКТИРОВАНИЕ ЗАМЕТКИ
# ============================================================================

@router.callback_query(F.data.startswith("note_edit:"))
async def callback_note_edit(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования заметки."""
    note_id = int(callback.data.split(":")[1])
    
    await state.update_data(edit_note_id=note_id)
    await state.set_state(NoteStates.waiting_for_edit_title)
    
    await callback.message.edit_text(
        "✏️ <b>Редактирование заметки</b>\n\n"
        "Введите новый заголовок или нажмите 'Пропустить' чтобы оставить текущий:",
        reply_markup=get_skip_keyboard("skip_edit_title")
    )
    await callback.answer()


@router.callback_query(F.data == "skip_edit_title", NoteStates.waiting_for_edit_title)
async def skip_edit_title(callback: CallbackQuery, state: FSMContext):
    """Пропуск редактирования заголовка."""
    await state.set_state(NoteStates.waiting_for_edit_content)
    await callback.message.edit_text(
        "Введите новое содержимое или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard("skip_edit_content")
    )
    await callback.answer()


@router.message(NoteStates.waiting_for_edit_title)
async def process_edit_title(message: Message, state: FSMContext):
    """Обработка нового заголовка."""
    await state.update_data(new_title=message.text)
    await state.set_state(NoteStates.waiting_for_edit_content)
    
    await message.answer(
        "Введите новое содержимое или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard("skip_edit_content")
    )


@router.callback_query(F.data == "skip_edit_content", NoteStates.waiting_for_edit_content)
async def skip_edit_content(callback: CallbackQuery, state: FSMContext, db: Database):
    """Пропуск редактирования содержимого."""
    await _finish_edit_note(callback.message, state, db, new_content=None, edit_message=True)
    await callback.answer()


@router.message(NoteStates.waiting_for_edit_content)
async def process_edit_content(message: Message, state: FSMContext, db: Database):
    """Обработка нового содержимого."""
    await _finish_edit_note(message, state, db, new_content=message.text, edit_message=False)


async def _finish_edit_note(message: Message, state: FSMContext, db: Database, new_content: str = None, edit_message: bool = False):
    """Завершение редактирования заметки."""
    data = await state.get_data()
    await state.clear()
    
    note_id = data["edit_note_id"]
    new_title = data.get("new_title")
    
    note_repo = NoteRepository(db)
    
    update_data = {}
    if new_title:
        update_data["title"] = new_title
    if new_content:
        update_data["content"] = new_content
    
    if update_data:
        await note_repo.update(note_id, **update_data)
    
    text = "✅ Заметка обновлена!"
    
    if edit_message:
        await message.edit_text(text, reply_markup=get_note_actions_keyboard(note_id))
    else:
        await message.answer(text, reply_markup=get_note_actions_keyboard(note_id))


# ============================================================================
# УДАЛЕНИЕ ЗАМЕТКИ
# ============================================================================

@router.callback_query(F.data.startswith("note_delete:"))
async def callback_note_delete(callback: CallbackQuery):
    """Подтверждение удаления заметки."""
    note_id = int(callback.data.split(":")[1])
    
    from bot.keyboards.builders import get_confirmation_keyboard
    
    await callback.message.edit_text(
        "🗑 <b>Удаление заметки</b>\n\n"
        "Вы уверены, что хотите удалить эту заметку?",
        reply_markup=get_confirmation_keyboard("note_delete", note_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("note_delete_confirm:"))
async def callback_note_delete_confirm(callback: CallbackQuery, user: User, db: Database):
    """Подтверждение удаления."""
    note_id = int(callback.data.split(":")[1])
    
    note_repo = NoteRepository(db)
    note = await note_repo.get_by_id(note_id)
    
    if not note or note.user_id != user.id:
        await callback.answer("Заметка не найдена", show_alert=True)
        return
    
    await note_repo.delete(note_id)
    
    await callback.message.edit_text(
        "✅ Заметка удалена!",
        reply_markup=get_notes_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("note_delete_cancel:"))
async def callback_note_delete_cancel(callback: CallbackQuery):
    """Отмена удаления."""
    note_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "❌ Удаление отменено.",
        reply_markup=get_note_actions_keyboard(note_id)
    )
    await callback.answer()