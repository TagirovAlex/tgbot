"""
Построители клавиатур.
"""

from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.timezone import POPULAR_TIMEZONES


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📝 Заметки", callback_data="notes_menu"),
        InlineKeyboardButton(text="⏰ Напоминания", callback_data="reminders_menu")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Шаблоны", callback_data="templates_menu"),
        InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="timezone_menu")
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
    )
    
    return builder.as_markup()


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню администратора."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="📜 Скрипты", callback_data="admin_scripts")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Логи", callback_data="admin_logs"),
        InlineKeyboardButton(text="🔄 Перезапуск", callback_data="admin_restart")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_notes_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню заметок."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Создать", callback_data="note_create"),
        InlineKeyboardButton(text="📋 Список", callback_data="notes_list")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Из шаблона", callback_data="note_from_template")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_reminders_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню напоминаний."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Создать", callback_data="reminder_create"),
        InlineKeyboardButton(text="📋 Список", callback_data="reminders_list")
    )
    builder.row(
        InlineKeyboardButton(text="⏰ Из шаблона", callback_data="reminder_from_template")
    )
    builder.row(
        InlineKeyboardButton(text="👥 В группу", callback_data="reminder_create_group")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_templates_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню шаблонов."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Создать", callback_data="template_create"),
        InlineKeyboardButton(text="📋 Список", callback_data="templates_list")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_note_actions_keyboard(note_id: int) -> InlineKeyboardMarkup:
    """Действия с заметкой."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"note_edit:{note_id}"
        ),
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"note_delete:{note_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="notes_list")
    )
    
    return builder.as_markup()


def get_reminder_actions_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    """Действия с напоминанием."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"reminder_edit:{reminder_id}"
        ),
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"reminder_delete:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏸ Деактивировать",
            callback_data=f"reminder_deactivate:{reminder_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="reminders_list")
    )
    
    return builder.as_markup()


def get_repeat_interval_keyboard() -> InlineKeyboardMarkup:
    """Выбор интервала повтора."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="Одноразово", callback_data="interval:0"),
        InlineKeyboardButton(text="Каждый час", callback_data="interval:60")
    )
    builder.row(
        InlineKeyboardButton(text="Ежедневно", callback_data="interval:1440"),
        InlineKeyboardButton(text="Еженедельно", callback_data="interval:10080")
    )
    builder.row(
        InlineKeyboardButton(text="Ежемесячно", callback_data="interval:43200")
    )
    builder.row(
        InlineKeyboardButton(text="« Отмена", callback_data="reminders_menu")
    )
    
    return builder.as_markup()


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Выбор часового пояса."""
    builder = InlineKeyboardBuilder()
    
    for tz_name, tz_label in POPULAR_TIMEZONES:
        builder.row(
            InlineKeyboardButton(
                text=tz_label,
                callback_data=f"tz:{tz_name}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_confirmation_keyboard(
    action: str,
    item_id: int
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Да",
            callback_data=f"{action}_confirm:{item_id}"
        ),
        InlineKeyboardButton(
            text="❌ Нет",
            callback_data=f"{action}_cancel:{item_id}"
        )
    )
    
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def get_skip_keyboard(callback_data: str = "skip") -> InlineKeyboardMarkup:
    """Кнопка пропуска."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data=callback_data)
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()



def get_pagination_keyboard(
    items: list,
    page: int,
    total_pages: int,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """Клавиатура с пагинацией."""
    builder = InlineKeyboardBuilder()
    
    # Кнопки элементов
    for item in items:
        builder.row(
            InlineKeyboardButton(
                text=item["text"],
                callback_data=f"{callback_prefix}_view:{item['id']}"
            )
        )
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="« Назад",
                callback_data=f"{callback_prefix}_page:{page - 1}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        )
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд »",
                callback_data=f"{callback_prefix}_page:{page + 1}"
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    return builder.as_markup()