"""
Обработчики для работы с шаблонами.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.database import Database
from database.repositories import TemplateRepository
from database.repositories.users import User
from bot.states import TemplateStates
from bot.keyboards.builders import (
    get_templates_menu_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
)
from utils.helpers import truncate_text

router = Router(name="templates")


@router.message(Command("templates"))
async def cmd_templates(message: Message):
    """Команда /templates."""
    await message.answer(
        "📋 <b>Шаблоны</b>\n\nВыберите действие:",
        reply_markup=get_templates_menu_keyboard()
    )


@router.callback_query(F.data == "templates_menu")
async def callback_templates_menu(callback: CallbackQuery, state: FSMContext):
    """Меню шаблонов."""
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>Шаблоны</b>\n\nВыберите действие:",
        reply_markup=get_templates_menu_keyboard()
    )
    await callback.answer()


# === Создание шаблона ===

@router.callback_query(F.data == "template_create")
async def callback_template_create(callback: CallbackQuery, state: FSMContext):
    """Начало создания шаблона."""
    await state.set_state(TemplateStates.waiting_for_type_select)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Для заметок", callback_data="template_type:note"),
        InlineKeyboardButton(text="⏰ Для напоминаний", callback_data="template_type:reminder")
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    
    await callback.message.edit_text(
        "📋 <b>Создание шаблона</b>\n\n"
        "Выберите тип шаблона:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("template_type:"), TemplateStates.waiting_for_type_select)
async def process_template_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа шаблона."""
    template_type = callback.data.split(":")[1]
    await state.update_data(template_type=template_type)
    await state.set_state(TemplateStates.waiting_for_name)
    
    await callback.message.edit_text(
        "📋 <b>Создание шаблона</b>\n\n"
        "Введите название шаблона:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(TemplateStates.waiting_for_name)
async def process_template_name(message: Message, state: FSMContext):
    """Обработка названия шаблона."""
    await state.update_data(name=message.text)
    await state.set_state(TemplateStates.waiting_for_title_template)
    
    await message.answer(
        "Введите шаблон заголовка.\n\n"
        "Доступные переменные:\n"
        "{{name}} - имя пользователя\n"
        "{{date}} - текущая дата\n"
        "{{time}} - текущее время\n\n"
        "Пример: Заметка от {{date}}",
        reply_markup=get_skip_keyboard("skip_title_template")
    )


@router.callback_query(F.data == "skip_title_template", TemplateStates.waiting_for_title_template)
async def skip_title_template(callback: CallbackQuery, state: FSMContext):
    """Пропуск шаблона заголовка."""
    await state.set_state(TemplateStates.waiting_for_content_template)
    await callback.message.edit_text(
        "Введите шаблон содержимого:",
        reply_markup=get_skip_keyboard("skip_content_template")
    )
    await callback.answer()


@router.message(TemplateStates.waiting_for_title_template)
async def process_title_template(message: Message, state: FSMContext):
    """Обработка шаблона заголовка."""
    await state.update_data(title_template=message.text)
    await state.set_state(TemplateStates.waiting_for_content_template)
    
    await message.answer(
        "Введите шаблон содержимого или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard("skip_content_template")
    )


@router.callback_query(F.data == "skip_content_template", TemplateStates.waiting_for_content_template)
async def skip_content_template(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Пропуск шаблона содержимого."""
    await _save_template(callback.message, state, user, db, content_template=None)
    await callback.answer()


@router.message(TemplateStates.waiting_for_content_template)
async def process_content_template(message: Message, state: FSMContext, user: User, db: Database):
    """Обработка шаблона содержимого."""
    await _save_template(message, state, user, db, content_template=message.text)


async def _save_template(message: Message, state: FSMContext, user: User, db: Database, content_template: str = None):
    """Сохранение шаблона."""
    data = await state.get_data()
    await state.clear()
    
    template_repo = TemplateRepository(db)
    await template_repo.create(
        user_id=user.id,
        name=data["name"],
        template_type=data["template_type"],
        title_template=data.get("title_template"),
        content_template=content_template
    )
    
    type_label = "📝 заметок" if data["template_type"] == "note" else "⏰ напоминаний"
    
    await message.answer(
        f"✅ Шаблон создан!\n\n"
        f"<b>{data['name']}</b>\n"
        f"Тип: для {type_label}",
        reply_markup=get_templates_menu_keyboard()
    )


# === Список шаблонов ===

@router.callback_query(F.data == "templates_list")
async def callback_templates_list(callback: CallbackQuery, user: User, db: Database):
    """Список шаблонов."""
    template_repo = TemplateRepository(db)
    templates = await template_repo.get_user_templates(user.id)
    
    if not templates:
        await callback.message.edit_text(
            "📋 <b>Ваши шаблоны</b>\n\n"
            "У вас пока нет шаблонов.",
            reply_markup=get_templates_menu_keyboard()
        )
        await callback.answer()
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    for template in templates:
        icon = "📝" if template.type == "note" else "⏰"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {template.name}",
                callback_data=f"template_view:{template.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="templates_menu"))
    
    await callback.message.edit_text(
        f"📋 <b>Ваши шаблоны</b> ({len(templates)})",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("template_view:"))
async def callback_template_view(callback: CallbackQuery, user: User, db: Database):
    """Просмотр шаблона."""
    template_id = int(callback.data.split(":")[1])
    
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    
    if not template or template.user_id != user.id:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    
    type_label = "📝 Для заметок" if template.type == "note" else "⏰ Для напоминаний"
    title_tpl = template.title_template or "(не задан)"
    content_tpl = template.content_template or "(не задан)"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"template_delete:{template.id}"
        )
    )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="templates_list"))
    
    await callback.message.edit_text(
        f"📋 <b>{template.name}</b>\n\n"
        f"Тип: {type_label}\n\n"
        f"<b>Шаблон заголовка:</b>\n{title_tpl}\n\n"
        f"<b>Шаблон содержимого:</b>\n{content_tpl}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("template_delete:"))
async def callback_template_delete(callback: CallbackQuery, user: User, db: Database):
    """Удаление шаблона."""
    template_id = int(callback.data.split(":")[1])
    
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    
    if not template or template.user_id != user.id:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    
    await template_repo.delete(template_id)
    
    await callback.message.edit_text(
        "✅ Шаблон удалён!",
        reply_markup=get_templates_menu_keyboard()
    )
    await callback.answer()