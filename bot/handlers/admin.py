"""
Обработчики для административных функций.
"""

import asyncio
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.database import Database
from database.repositories import UserRepository
from database.repositories.users import User
from bot.filters import IsAdminFilter
from bot.keyboards.builders import (
    get_admin_menu_keyboard,
    get_main_menu_keyboard,
)
from services.script_runner import ScriptRunnerService

logger = logging.getLogger(__name__)

router = Router(name="admin")


# ============================================================================
# ПАНЕЛЬ АДМИНИСТРАТОРА
# ============================================================================

@router.message(Command("admin"), IsAdminFilter())
async def cmd_admin(message: Message):
    """Команда /admin - панель администратора."""
    await message.answer(
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )


@router.callback_query(F.data == "admin_menu", IsAdminFilter())
async def callback_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Меню администратора."""
    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


# ============================================================================
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# ============================================================================

@router.callback_query(F.data == "admin_users", IsAdminFilter())
async def callback_admin_users(callback: CallbackQuery, db: Database):
    """Список пользователей."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all_users()
    
    builder = InlineKeyboardBuilder()
    
    if not users:
        await callback.message.edit_text(
            "👥 <b>Пользователи</b>\n\n"
            "Список пользователей пуст.",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for u in users[:20]:  # Ограничиваем список
        icon = "👑" if u.is_admin else "👤"
        username = u.username or u.full_name or f"ID:{u.telegram_id}"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {username}",
                callback_data=f"admin_user_view:{u.id}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        f"👥 <b>Пользователи</b> ({len(users)})\n\n"
        "Выберите пользователя для управления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_view:"), IsAdminFilter())
async def callback_admin_user_view(callback: CallbackQuery, db: Database):
    """Просмотр информации о пользователе."""
    user_id = int(callback.data.split(":")[1])
    
    user_repo = UserRepository(db)
    u = await user_repo.get_by_id(user_id)
    
    if not u:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    
    if u.is_admin:
        builder.row(
            InlineKeyboardButton(
                text="❌ Снять права админа",
                callback_data=f"admin_revoke:{u.id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✅ Назначить админом",
                callback_data=f"admin_grant:{u.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="« К списку", callback_data="admin_users"),
        InlineKeyboardButton(text="« Меню", callback_data="admin_menu")
    )
    
    status = "👑 Администратор" if u.is_admin else "👤 Пользователь"
    username_display = f"@{u.username}" if u.username else "не указан"
    
    await callback.message.edit_text(
        f"<b>Информация о пользователе</b>\n\n"
        f"🆔 ID в БД: {u.id}\n"
        f"🆔 Telegram ID: <code>{u.telegram_id}</code>\n"
        f"👤 Username: {username_display}\n"
        f"📛 Имя: {u.full_name or 'не указано'}\n"
        f"🌍 Часовой пояс: {u.timezone}\n"
        f"🔑 Статус: {status}\n"
        f"📅 Регистрация: {u.created_at}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_grant:"), IsAdminFilter())
async def callback_admin_grant(callback: CallbackQuery, db: Database):
    """Назначить права администратора."""
    user_id = int(callback.data.split(":")[1])
    
    user_repo = UserRepository(db)
    u = await user_repo.get_by_id(user_id)
    
    if not u:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    await user_repo.set_admin(user_id, True)
    
    logger.info(f"Пользователю {u.telegram_id} ({u.username}) выданы права администратора")
    
    await callback.answer("✅ Права администратора выданы!", show_alert=True)
    
    # Обновляем отображение
    # Получаем обновлённые данные
    u = await user_repo.get_by_id(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Снять права админа",
            callback_data=f"admin_revoke:{u.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« К списку", callback_data="admin_users"),
        InlineKeyboardButton(text="« Меню", callback_data="admin_menu")
    )
    
    username_display = f"@{u.username}" if u.username else "не указан"
    
    await callback.message.edit_text(
        f"<b>Информация о пользователе</b>\n\n"
        f"🆔 ID в БД: {u.id}\n"
        f"🆔 Telegram ID: <code>{u.telegram_id}</code>\n"
        f"👤 Username: {username_display}\n"
        f"📛 Имя: {u.full_name or 'не указано'}\n"
        f"🌍 Часовой пояс: {u.timezone}\n"
        f"🔑 Статус: 👑 Администратор\n"
        f"📅 Регистрация: {u.created_at}",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin_revoke:"), IsAdminFilter())
async def callback_admin_revoke(callback: CallbackQuery, db: Database, user: User):
    """Снять права администратора."""
    user_id = int(callback.data.split(":")[1])
    
    user_repo = UserRepository(db)
    u = await user_repo.get_by_id(user_id)
    
    if not u:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    # Нельзя снять права у самого себя
    if u.telegram_id == callback.from_user.id:
        await callback.answer("❌ Нельзя снять права у самого себя!", show_alert=True)
        return
    
    # Нельзя снять права у админа из конфига
    import config
    if u.telegram_id in config.ADMIN_IDS:
        await callback.answer("❌ Нельзя снять права у главного администратора!", show_alert=True)
        return
    
    await user_repo.set_admin(user_id, False)
    
    logger.info(f"У пользователя {u.telegram_id} ({u.username}) отозваны права администратора")
    
    await callback.answer("✅ Права администратора сняты!", show_alert=True)
    
    # Обновляем отображение
    u = await user_repo.get_by_id(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Назначить админом",
            callback_data=f"admin_grant:{u.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« К списку", callback_data="admin_users"),
        InlineKeyboardButton(text="« Меню", callback_data="admin_menu")
    )
    
    username_display = f"@{u.username}" if u.username else "не указан"
    
    await callback.message.edit_text(
        f"<b>Информация о пользователе</b>\n\n"
        f"🆔 ID в БД: {u.id}\n"
        f"🆔 Telegram ID: <code>{u.telegram_id}</code>\n"
        f"👤 Username: {username_display}\n"
        f"📛 Имя: {u.full_name or 'не указано'}\n"
        f"🌍 Часовой пояс: {u.timezone}\n"
        f"🔑 Статус: 👤 Пользователь\n"
        f"📅 Регистрация: {u.created_at}",
        reply_markup=builder.as_markup()
    )


# ============================================================================
# УПРАВЛЕНИЕ СКРИПТАМИ
# ============================================================================

@router.callback_query(F.data == "admin_scripts", IsAdminFilter())
async def callback_admin_scripts(callback: CallbackQuery, db: Database):
    """Список доступных скриптов."""
    script_service = ScriptRunnerService(db)
    scripts = await script_service.get_available_scripts()
    
    builder = InlineKeyboardBuilder()
    
    if not scripts:
        import config
        await callback.message.edit_text(
            "📜 <b>Скрипты</b>\n\n"
            "Нет доступных скриптов.\n\n"
            f"Положите скрипты (.sh, .py, .bash) в папку:\n"
            f"<code>{config.SCRIPTS_DIR}</code>",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for script in scripts:
        # Определяем иконку по расширению
        if script.endswith('.py'):
            icon = "🐍"
        elif script.endswith('.sh') or script.endswith('.bash'):
            icon = "🔧"
        else:
            icon = "📄"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {script}",
                callback_data=f"script_info:{script}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        f"📜 <b>Доступные скрипты</b> ({len(scripts)})\n\n"
        "Выберите скрипт для просмотра информации и запуска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("script_info:"), IsAdminFilter())
async def callback_script_info(callback: CallbackQuery, db: Database):
    """Информация о скрипте и кнопка запуска."""
    script_name = callback.data.split(":", 1)[1]
    
    import config
    from pathlib import Path
    
    script_path = config.SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        await callback.answer("Скрипт не найден", show_alert=True)
        return
    
    # Получаем информацию о файле
    stat = script_path.stat()
    size = stat.st_size
    
    # Определяем тип
    if script_name.endswith('.py'):
        script_type = "Python скрипт"
    elif script_name.endswith('.sh') or script_name.endswith('.bash'):
        script_type = "Bash скрипт"
    else:
        script_type = "Исполняемый файл"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="▶️ Запустить",
            callback_data=f"script_run:{script_name}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« К списку", callback_data="admin_scripts"),
        InlineKeyboardButton(text="« Меню", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(
        f"📜 <b>Информация о скрипте</b>\n\n"
        f"📄 Файл: <code>{script_name}</code>\n"
        f"📁 Тип: {script_type}\n"
        f"📊 Размер: {size} байт\n"
        f"📍 Путь: <code>{script_path}</code>\n\n"
        f"⚠️ <b>Внимание:</b> скрипт будет выполнен на сервере!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("script_run:"), IsAdminFilter())
async def callback_script_run(callback: CallbackQuery, db: Database):
    """Подтверждение запуска скрипта."""
    script_name = callback.data.split(":", 1)[1]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, запустить",
            callback_data=f"script_execute:{script_name}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"script_info:{script_name}"
        )
    )
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение запуска</b>\n\n"
        f"Скрипт: <code>{script_name}</code>\n\n"
        f"Вы уверены, что хотите запустить этот скрипт?\n"
        f"Скрипт будет выполнен на сервере.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("script_execute:"), IsAdminFilter())
async def callback_script_execute(callback: CallbackQuery, db: Database, user: User):
    """Выполнение скрипта."""
    script_name = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        f"⏳ <b>Выполнение скрипта...</b>\n\n"
        f"Скрипт: <code>{script_name}</code>\n\n"
        f"Пожалуйста, подождите..."
    )
    
    script_service = ScriptRunnerService(db)
    
    logger.info(f"Админ {user.telegram_id} запустил скрипт: {script_name}")
    
    try:
        result = await script_service.run_script(script_name, timeout=120)
        
        # Формируем вывод
        status_icon = "✅" if result.success else "❌"
        status_text = "Успешно" if result.success else "Ошибка"
        
        output = f"{status_icon} <b>Результат выполнения</b>\n\n"
        output += f"📄 Скрипт: <code>{script_name}</code>\n"
        output += f"📊 Статус: {status_text}\n"
        output += f"🔢 Код возврата: {result.return_code}\n\n"
        
        if result.stdout:
            stdout = result.stdout[:3000]  # Ограничиваем вывод
            if len(result.stdout) > 3000:
                stdout += "\n... (вывод обрезан)"
            output += f"<b>📤 Вывод:</b>\n<pre>{stdout}</pre>\n\n"
        
        if result.stderr:
            stderr = result.stderr[:1000]
            if len(result.stderr) > 1000:
                stderr += "\n... (вывод обрезан)"
            output += f"<b>⚠️ Ошибки:</b>\n<pre>{stderr}</pre>"
        
        if not result.stdout and not result.stderr:
            output += "<i>Скрипт не вернул вывода</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔄 Запустить снова",
                callback_data=f"script_run:{script_name}"
            )
        )
        builder.row(
            InlineKeyboardButton(text="« К списку", callback_data="admin_scripts"),
            InlineKeyboardButton(text="« Меню", callback_data="admin_menu")
        )
        
        await callback.message.edit_text(
            output[:4000],  # Telegram limit
            reply_markup=builder.as_markup()
        )
        
    except FileNotFoundError:
        await callback.message.edit_text(
            f"❌ <b>Ошибка</b>\n\n"
            f"Скрипт <code>{script_name}</code> не найден.",
            reply_markup=get_admin_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка выполнения скрипта {script_name}: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка выполнения</b>\n\n"
            f"Скрипт: <code>{script_name}</code>\n"
            f"Ошибка: {str(e)}",
            reply_markup=get_admin_menu_keyboard()
        )
    
    await callback.answer()


# ============================================================================
# ПРОСМОТР ЛОГОВ
# ============================================================================

@router.callback_query(F.data == "admin_logs", IsAdminFilter())
async def callback_admin_logs(callback: CallbackQuery, db: Database):
    """Просмотр последних логов действий."""
    rows = await db.fetch_all(
        """
        SELECT al.*, u.username, u.telegram_id, u.full_name
        FROM action_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 30
        """
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_logs")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin_menu")
    )
    
    if not rows:
        await callback.message.edit_text(
            "📊 <b>Логи действий</b>\n\n"
            "Логи пусты.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    logs_text = "📊 <b>Последние действия</b>\n\n"
    
    for row in rows:
        # Определяем имя пользователя
        if row["username"]:
            username = f"@{row['username']}"
        elif row["full_name"]:
            username = row["full_name"]
        elif row["telegram_id"]:
            username = f"ID:{row['telegram_id']}"
        else:
            username = "Неизвестный"
        
        action = row["action"]
        details = row["details"][:40] + "..." if row["details"] and len(row["details"]) > 40 else (row["details"] or "")
        
        # Иконки для разных действий
        if action == "message":
            icon = "💬"
        elif action == "callback":
            icon = "🔘"
        elif action == "document":
            icon = "📎"
        elif action == "photo":
            icon = "🖼"
        else:
            icon = "📝"
        
        logs_text += f"{icon} <b>{username}</b>: {action}"
        if details:
            logs_text += f"\n   └ <i>{details}</i>"
        logs_text += "\n"
    
    await callback.message.edit_text(
        logs_text[:4000],
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ============================================================================
# ПЕРЕЗАПУСК БОТА
# ============================================================================

@router.callback_query(F.data == "admin_restart", IsAdminFilter())
async def callback_admin_restart(callback: CallbackQuery):
    """Подтверждение перезапуска."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, перезапустить", callback_data="restart_confirm"),
        InlineKeyboardButton(text="❌ Нет", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(
        "🔄 <b>Перезапуск бота</b>\n\n"
        "⚠️ Вы уверены, что хотите перезапустить бота?\n\n"
        "• Все активные сессии будут прерваны\n"
        "• Состояния диалогов будут сброшены\n"
        "• Бот будет недоступен несколько секунд",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "restart_confirm", IsAdminFilter())
async def callback_restart_confirm(callback: CallbackQuery, user: User):
    """Выполнение перезапуска."""
    logger.info(f"Админ {user.telegram_id} инициировал перезапуск бота")
    
    await callback.message.edit_text(
        "🔄 <b>Бот перезапускается...</b>\n\n"
        "Подождите несколько секунд."
    )
    await callback.answer()
    
    # Импортируем функцию получения приложения
    from main import get_bot_app
    
    bot_app = get_bot_app()
    if bot_app:
        # Запускаем перезапуск в фоне
        asyncio.create_task(bot_app.restart())
    else:
        await callback.message.edit_text(
            "❌ Не удалось выполнить перезапуск.\n"
            "Перезапустите бота вручную.",
            reply_markup=get_admin_menu_keyboard()
        )


# ============================================================================
# ТЕКСТОВЫЕ КОМАНДЫ АДМИНИСТРАТОРА
# ============================================================================

@router.message(Command("users"), IsAdminFilter())
async def cmd_users(message: Message, db: Database):
    """Команда /users - быстрый просмотр списка пользователей."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all_users()
    
    if not users:
        await message.answer("👥 Список пользователей пуст.")
        return
    
    text = f"👥 <b>Пользователи</b> ({len(users)})\n\n"
    
    admins = [u for u in users if u.is_admin]
    regular = [u for u in users if not u.is_admin]
    
    if admins:
        text += "<b>👑 Администраторы:</b>\n"
        for u in admins:
            username = f"@{u.username}" if u.username else u.full_name or f"ID:{u.telegram_id}"
            text += f"  • {username}\n"
        text += "\n"
    
    text += f"<b>👤 Пользователи:</b> {len(regular)}\n"
    
    for u in regular[:15]:
        username = f"@{u.username}" if u.username else u.full_name or f"ID:{u.telegram_id}"
        text += f"  • {username}\n"
    
    if len(regular) > 15:
        text += f"  ... и ещё {len(regular) - 15}\n"
    
    text += "\nИспользуйте /admin для управления."
    
    await message.answer(text)


@router.message(Command("scripts"), IsAdminFilter())
async def cmd_scripts(message: Message, db: Database):
    """Команда /scripts - список скриптов."""
    script_service = ScriptRunnerService(db)
    scripts = await script_service.get_available_scripts()
    
    if not scripts:
        import config
        await message.answer(
            "📜 <b>Скрипты</b>\n\n"
            "Нет доступных скриптов.\n"
            f"Папка: <code>{config.SCRIPTS_DIR}</code>"
        )
        return
    
    text = f"📜 <b>Доступные скрипты</b> ({len(scripts)})\n\n"
    for script in scripts:
        if script.endswith('.py'):
            icon = "🐍"
        elif script.endswith('.sh') or script.endswith('.bash'):
            icon = "🔧"
        else:
            icon = "📄"
        text += f"{icon} <code>{script}</code>\n"
    
    text += "\nИспользуйте /admin → Скрипты для запуска."
    
    await message.answer(text)


@router.message(Command("restart"), IsAdminFilter())
async def cmd_restart(message: Message):
    """Команда /restart - перезапуск бота."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="restart_confirm"),
        InlineKeyboardButton(text="❌ Нет", callback_data="admin_menu")
    )
    
    await message.answer(
        "🔄 <b>Перезапуск бота</b>\n\n"
        "Вы уверены?",
        reply_markup=builder.as_markup()
    )


@router.message(Command("logs"), IsAdminFilter())
async def cmd_logs(message: Message, db: Database):
    """Команда /logs - последние логи."""
    rows = await db.fetch_all(
        """
        SELECT al.*, u.username, u.telegram_id
        FROM action_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 20
        """
    )
    
    if not rows:
        await message.answer("📊 Логи пусты.")
        return
    
    text = "📊 <b>Последние действия</b>\n\n"
    
    for row in rows:
        username = row["username"] or f"ID:{row['telegram_id']}" if row["telegram_id"] else "?"
        action = row["action"]
        details = (row["details"][:25] + "...") if row["details"] and len(row["details"]) > 25 else (row["details"] or "")
        
        text += f"• <b>{username}</b>: {action}"
        if details:
            text += f" - {details}"
        text += "\n"
    
    await message.answer(text)


# ============================================================================
# ОБРАБОТКА НЕ-АДМИНОВ
# ============================================================================

@router.message(Command("admin"))
async def cmd_admin_denied(message: Message):
    """Отказ в доступе для не-админов."""
    await message.answer(
        "🔒 <b>Доступ запрещён</b>\n\n"
        "У вас нет прав администратора."
    )


@router.message(Command("users"))
async def cmd_users_denied(message: Message):
    """Отказ для не-админов."""
    await message.answer("🔒 У вас нет прав для этой команды.")


@router.message(Command("scripts"))
async def cmd_scripts_denied(message: Message):
    """Отказ для не-админов."""
    await message.answer("🔒 У вас нет прав для этой команды.")


@router.message(Command("restart"))
async def cmd_restart_denied(message: Message):
    """Отказ для не-админов."""
    await message.answer("🔒 У вас нет прав для этой команды.")


@router.message(Command("logs"))
async def cmd_logs_denied(message: Message):
    """Отказ для не-админов."""
    await message.answer("🔒 У вас нет прав для этой команды.")