@router.callback_query(F.data.startswith("admin_revoke:"))
async def callback_admin_revoke(callback: CallbackQuery, db: Database):
    """Отозвать права админа."""
    user_id = int(callback.data.split(":")[1])
    
    user_repo = UserRepository(db)
    await user_repo.set_admin(user_id, False)
    
    await callback.answer("❌ Права администратора отозваны", show_alert=True)
    
    # Обновляем информацию
    await callback_admin_user_view(callback, db)


# === Выполнение скриптов ===

@router.callback_query(F.data == "admin_scripts")
async def callback_admin_scripts(callback: CallbackQuery, db: Database):
    """Список доступных скриптов."""
    script_service = ScriptRunnerService(db)
    scripts = await script_service.get_available_scripts()
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    if not scripts:
        await callback.message.edit_text(
            "📜 <b>Скрипты</b>\n\n"
            "Нет доступных скриптов.\n"
            f"Положите скрипты в папку scripts/",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for script in scripts:
        builder.row(
            InlineKeyboardButton(
                text=f"📄 {script}",
                callback_data=f"script_run:{script}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="admin_menu"))
    
    await callback.message.edit_text(
        f"📜 <b>Доступные скрипты</b> ({len(scripts)})\n\n"
        "Выберите скрипт для запуска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("script_run:"))
async def callback_script_run(callback: CallbackQuery, db: Database):
    """Подтверждение запуска скрипта."""
    script_name = callback.data.split(":", 1)[1]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Запустить",
            callback_data=f"script_confirm:{script_name}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin_scripts"
        )
    )
    
    await callback.message.edit_text(
        f"📜 <b>Запуск скрипта</b>\n\n"
        f"Скрипт: <code>{script_name}</code>\n\n"
        f"⚠️ Вы уверены, что хотите запустить этот скрипт?",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("script_confirm:"))
async def callback_script_confirm(callback: CallbackQuery, db: Database):
    """Выполнение скрипта."""
    script_name = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        f"⏳ Выполняется скрипт <code>{script_name}</code>...\n\n"
        "Пожалуйста, подождите."
    )
    
    script_service = ScriptRunnerService(db)
    
    try:
        result = await script_service.run_script(script_name)
        
        # Формируем вывод
        status = "✅ Успешно" if result.success else "❌ Ошибка"
        
        output = f"📜 <b>Результат выполнения</b>\n\n"
        output += f"Скрипт: <code>{script_name}</code>\n"
        output += f"Статус: {status}\n"
        output += f"Код возврата: {result.return_code}\n\n"
        
        if result.stdout:
            stdout = result.stdout[:2000]  # Ограничиваем вывод
            output += f"<b>Вывод:</b>\n<pre>{stdout}</pre>\n\n"
        
        if result.stderr:
            stderr = result.stderr[:1000]
            output += f"<b>Ошибки:</b>\n<pre>{stderr}</pre>"
        
        await callback.message.edit_text(
            output,
            reply_markup=get_admin_menu_keyboard()
        )
        
    except FileNotFoundError:
        await callback.message.edit_text(
            f"❌ Скрипт <code>{script_name}</code> не найден.",
            reply_markup=get_admin_menu_keyboard()
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка выполнения: {str(e)}",
            reply_markup=get_admin_menu_keyboard()
        )
    
    await callback.answer()


# === Просмотр логов ===

@router.callback_query(F.data == "admin_logs")
async def callback_admin_logs(callback: CallbackQuery, db: Database):
    """Просмотр последних логов."""
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
        await callback.message.edit_text(
            "📊 <b>Логи действий</b>\n\n"
            "Логи пусты.",
            reply_markup=get_admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    logs_text = "📊 <b>Последние действия</b>\n\n"
    
    for row in rows:
        username = row["username"] or str(row["telegram_id"]) or "Unknown"
        action = row["action"]
        details = row["details"][:50] if row["details"] else ""
        time = row["created_at"]
        
        logs_text += f"• <b>{username}</b>: {action}"
        if details:
            logs_text += f" - {details}"
        logs_text += f"\n  <i>{time}</i>\n\n"
    
    await callback.message.edit_text(
        logs_text[:4000],  # Telegram limit
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


# === Перезапуск бота ===

@router.callback_query(F.data == "admin_restart")
async def callback_admin_restart(callback: CallbackQuery):
    """Подтверждение перезапуска."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, перезапустить", callback_data="restart_confirm"),
        InlineKeyboardButton(text="❌ Нет", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(
        "🔄 <b>Перезапуск бота</b>\n\n"
        "⚠️ Вы уверены, что хотите перезапустить бота?\n"
        "Все активные сессии будут прерваны.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "restart_confirm")
async def callback_restart_confirm(callback: CallbackQuery):
    """Выполнение перезапуска."""
    await callback.message.edit_text(
        "🔄 Бот перезапускается...\n\n"
        "Подождите несколько секунд."
    )
    await callback.answer()
    
    # Получаем доступ к приложению через dispatcher
    bot_app = callback.bot.get("bot_app")
    if bot_app:
        # Запускаем перезапуск в фоне
        asyncio.create_task(bot_app.restart())
    else:
        await callback.message.edit_text(
            "❌ Не удалось выполнить перезапуск.\n"
            "Перезапустите бота вручную.",
            reply_markup=get_admin_menu_keyboard()
        )


# === Команды администратора ===

@router.message(Command("users"))
async def cmd_users(message: Message, db: Database):
    """Команда /users - список пользователей."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all_users()
    
    text = f"👥 <b>Пользователи</b> ({len(users)})\n\n"
    
    for u in users[:30]:
        icon = "👑" if u.is_admin else "👤"
        username = f"@{u.username}" if u.username else u.full_name or "Без имени"
        text += f"{icon} {username} (ID: {u.telegram_id})\n"
    
    if len(users) > 30:
        text += f"\n... и ещё {len(users) - 30} пользователей"
    
    await message.answer(text)


@router.message(Command("scripts"))
async def cmd_scripts(message: Message, db: Database):
    """Команда /scripts - список скриптов."""
    script_service = ScriptRunnerService(db)
    scripts = await script_service.get_available_scripts()
    
    if not scripts:
        await message.answer(
            "📜 <b>Скрипты</b>\n\n"
            "Нет доступных скриптов."
        )
        return
    
    text = f"📜 <b>Доступные скрипты</b> ({len(scripts)})\n\n"
    for script in scripts:
        text += f"• <code>{script}</code>\n"
    
    text += "\nИспользуйте меню /admin для запуска."
    
    await message.answer(text)


@router.message(Command("restart"))
async def cmd_restart(message: Message):
    """Команда /restart - перезапуск бота."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="restart_confirm"),
        InlineKeyboardButton(text="❌ Нет", callback_data="admin_menu")
    )
    
    await message.answer(
        "🔄 Перезапустить бота?",
        reply_markup=builder.as_markup()
    )