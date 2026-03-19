"""
Обработчики для AI чата с Ollama LLM.

Разграничение прав:
- Пользователи: чат с AI, выбор режима, очистка истории
- Администраторы: управление моделями, установка активной модели
"""

import asyncio
import logging
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.enums import ChatAction

from database.database import Database
from database.repositories.users import User
from services.ollama_service import OllamaService, init_ollama_service
from bot.states.states import AIStates
from bot.filters.admin import IsAdminFilter
from bot.keyboards.builders import get_cancel_keyboard

logger = logging.getLogger(__name__)

router = Router(name="ai_chat")

_service: Optional[OllamaService] = None


def get_service(db: Database) -> OllamaService:
    """Получить или создать сервис."""
    global _service
    if _service is None:
        _service = init_ollama_service(db)
    return _service


# ============================================================================
# КЛАВИАТУРЫ
# ============================================================================

def get_ai_menu_keyboard(is_admin: bool = False):
    """Клавиатура меню AI."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💬 Начать чат", callback_data="ai_start_chat"),
        InlineKeyboardButton(text="🔄 Очистить историю", callback_data="ai_clear")
    )
    builder.row(
        InlineKeyboardButton(text="🎭 Режим", callback_data="ai_mode"),
        InlineKeyboardButton(text="ℹ️ Статус", callback_data="ai_status")
    )
    
    # Кнопка управления моделями только для админов
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Управление моделями", callback_data="ai_admin_models")
        )
    
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_mode_keyboard():
    """Клавиатура выбора режима."""
    builder = InlineKeyboardBuilder()
    modes = [
        ("💬 Обычный", "ai_set_mode:default"),
        ("💻 Программист", "ai_set_mode:coding"),
        ("✨ Креативный", "ai_set_mode:creative"),
        ("🌐 Переводчик", "ai_set_mode:translator"),
    ]
    for text, callback in modes:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="ai_menu"))
    return builder.as_markup()


def get_chat_keyboard():
    """Клавиатура во время чата."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Очистить", callback_data="ai_clear"),
        InlineKeyboardButton(text="🎭 Режим", callback_data="ai_mode")
    )
    builder.row(
        InlineKeyboardButton(text="🛑 Завершить чат", callback_data="ai_stop")
    )
    return builder.as_markup()


def get_admin_models_keyboard():
    """Клавиатура управления моделями (для админов)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список моделей", callback_data="ai_admin_list_models"),
        InlineKeyboardButton(text="✅ Выбрать активную", callback_data="ai_admin_select_model")
    )
    builder.row(
        InlineKeyboardButton(text="📥 Скачать модель", callback_data="ai_admin_pull_model"),
        InlineKeyboardButton(text="🗑 Удалить модель", callback_data="ai_admin_delete_model")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="ai_menu")
    )
    return builder.as_markup()


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def is_user_admin(user: User) -> bool:
    """Проверить, является ли пользователь администратором."""
    import config
    return user.is_admin or user.telegram_id in config.ADMIN_IDS


# ============================================================================
# КОМАНДЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

@router.message(Command("ai"))
async def cmd_ai(message: Message, state: FSMContext, user: User, db: Database):
    """Команда /ai."""
    service = get_service(db)
    
    if not await service.is_available():
        await message.answer(
            "❌ <b>AI сервис недоступен</b>\n\n"
            "Обратитесь к администратору."
        )
        return
    
    text = message.text.replace("/ai", "").strip()
    
    if text:
        # Быстрый вопрос
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        result = await service.chat(user_id=user.id, message=text)
        
        if result.success:
            response_text = result.content
            if len(response_text) > 4000:
                response_text = response_text[:4000] + "...\n\n<i>(ответ обрезан)</i>"
            
            await message.answer(
                f"🤖 {response_text}\n\n"
                f"<i>⏱ {result.total_duration:.1f}s | 📊 {result.response_tokens} токенов</i>",
                reply_markup=get_chat_keyboard()
            )
        else:
            await message.answer(f"❌ Ошибка: {result.error}")
    else:
        # Показываем меню
        admin = is_user_admin(user)
        active_model = await service.get_active_model()
        
        await message.answer(
            f"🤖 <b>AI Ассистент</b>\n\n"
            f"Модель: <code>{active_model}</code>\n\n"
            f"Напишите <code>/ai ваш вопрос</code>\n"
            f"или выберите действие:",
            reply_markup=get_ai_menu_keyboard(is_admin=admin)
        )


@router.message(Command("ai_clear"))
async def cmd_ai_clear(message: Message, user: User, db: Database):
    """Очистить историю чата."""
    service = get_service(db)
    service.clear_session(user.id)
    await message.answer("🔄 История чата очищена.")


@router.callback_query(F.data == "ai_menu")
async def callback_ai_menu(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Меню AI."""
    await state.clear()
    
    service = get_service(db)
    admin = is_user_admin(user)
    active_model = await service.get_active_model()
    
    await callback.message.edit_text(
        f"🤖 <b>AI Ассистент</b>\n\n"
        f"Модель: <code>{active_model}</code>\n\n"
        f"Выберите действие:",
        reply_markup=get_ai_menu_keyboard(is_admin=admin)
    )
    await callback.answer()


@router.callback_query(F.data == "ai_start_chat")
async def callback_ai_start_chat(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать чат."""
    service = get_service(db)
    
    if not await service.is_available():
        await callback.answer("❌ AI сервис недоступен", show_alert=True)
        return
    
    await state.set_state(AIStates.chatting)
    
    active_model = await service.get_active_model()
    
    await callback.message.edit_text(
        f"💬 <b>Режим чата</b>\n\n"
        f"Модель: <code>{active_model}</code>\n\n"
        f"Напишите ваш вопрос или сообщение.\n"
        f"Я запоминаю контекст беседы.\n\n"
        f"<i>Для выхода нажмите «Завершить чат»</i>",
        reply_markup=get_chat_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "ai_clear")
async def callback_ai_clear(callback: CallbackQuery, user: User, db: Database):
    """Очистить историю."""
    service = get_service(db)
    service.clear_session(user.id)
    await callback.answer("🔄 История очищена", show_alert=True)


@router.callback_query(F.data == "ai_mode")
async def callback_ai_mode(callback: CallbackQuery):
    """Выбор режима."""
    await callback.message.edit_text(
        "🎭 <b>Выберите режим AI:</b>\n\n"
        "• <b>Обычный</b> — универсальный помощник\n"
        "• <b>Программист</b> — помощь с кодом\n"
        "• <b>Креативный</b> — тексты и творчество\n"
        "• <b>Переводчик</b> — перевод текстов",
        reply_markup=get_mode_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai_set_mode:"))
async def callback_ai_set_mode(callback: CallbackQuery, user: User, db: Database):
    """Установить режим."""
    mode = callback.data.split(":")[1]
    
    service = get_service(db)
    service.set_session_mode(user.id, mode)
    
    mode_names = {
        "default": "💬 Обычный",
        "coding": "💻 Программист",
        "creative": "✨ Креативный",
        "translator": "🌐 Переводчик",
    }
    
    await callback.answer(f"Режим: {mode_names.get(mode, mode)}", show_alert=True)
    
    await callback.message.edit_text(
        f"✅ Режим изменён: <b>{mode_names.get(mode, mode)}</b>\n\n"
        f"История чата очищена.\n"
        f"Напишите сообщение для начала.",
        reply_markup=get_chat_keyboard()
    )


@router.callback_query(F.data == "ai_status")
async def callback_ai_status(callback: CallbackQuery, user: User, db: Database):
    """Статус AI."""
    service = get_service(db)
    
    is_available = await service.is_available()
    status = "✅ Онлайн" if is_available else "❌ Недоступен"
    
    active_model = await service.get_active_model()
    session_info = service.get_session_info(user.id)
    
    admin = is_user_admin(user)
    
    text = f"🤖 <b>Статус AI</b>\n\n"
    text += f"Сервер: {status}\n"
    text += f"Активная модель: <code>{active_model}</code>\n"
    text += f"Таймаут: {service.timeout}s\n\n"
    
    if session_info:
        text += f"<b>Ваша сессия:</b>\n"
        text += f"Сообщений: {session_info['messages_count']}\n"
    else:
        text += "<i>Сессия не активна</i>"
    
    await callback.message.edit_text(
        text, 
        reply_markup=get_ai_menu_keyboard(is_admin=admin)
    )
    await callback.answer()


@router.callback_query(F.data == "ai_stop")
async def callback_ai_stop(callback: CallbackQuery, state: FSMContext, user: User, db: Database):
    """Завершить чат."""
    await state.clear()
    
    admin = is_user_admin(user)
    
    await callback.message.edit_text(
        "👋 Чат завершён.\n\n"
        "История сохранена. Используйте /ai чтобы продолжить.",
        reply_markup=get_ai_menu_keyboard(is_admin=admin)
    )
    await callback.answer()


@router.message(AIStates.chatting)
async def process_chat_message(message: Message, state: FSMContext, user: User, db: Database):
    """Обработка сообщений в режиме чата."""
    service = get_service(db)
    
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    result = await service.chat(user_id=user.id, message=message.text)
    
    if result.success:
        response_text = result.content
        
        if len(response_text) > 4000:
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await message.answer(
                        f"🤖 {part}\n\n"
                        f"<i>⏱ {result.total_duration:.1f}s</i>",
                        reply_markup=get_chat_keyboard()
                    )
                else:
                    await message.answer(f"🤖 {part}")
                    await asyncio.sleep(0.3)
        else:
            await message.answer(
                f"🤖 {response_text}\n\n"
                f"<i>⏱ {result.total_duration:.1f}s | 📊 {result.response_tokens} токенов</i>",
                reply_markup=get_chat_keyboard()
            )
    else:
        await message.answer(
            f"❌ Ошибка: {result.error}\n\n"
            "Попробуйте ещё раз или очистите историю.",
            reply_markup=get_chat_keyboard()
        )


# ============================================================================
# КОМАНДЫ АДМИНИСТРАТОРА - УПРАВЛЕНИЕ МОДЕЛЯМИ
# ============================================================================

@router.callback_query(F.data == "ai_admin_models", IsAdminFilter())
async def callback_ai_admin_models(callback: CallbackQuery):
    """Меню управления моделями (только для админов)."""
    await callback.message.edit_text(
        "⚙️ <b>Управление моделями</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_models_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "ai_admin_list_models", IsAdminFilter())
async def callback_ai_admin_list_models(callback: CallbackQuery, db: Database):
    """Список установленных моделей."""
    service = get_service(db)
    models = await service.list_models()
    active_model = await service.get_active_model()
    
    if not models:
        await callback.message.edit_text(
            "📋 <b>Установленные модели</b>\n\n"
            "Нет установленных моделей.\n"
            "Скачайте модель через меню.",
            reply_markup=get_admin_models_keyboard()
        )
        await callback.answer()
        return
    
    text = f"📋 <b>Установленные модели</b>\n\n"
    text += f"🟢 Активная: <code>{active_model}</code>\n\n"
    
    for model in models:
        name = model.get("name", "unknown")
        size = model.get("size", 0)
        size_gb = size / (1024 ** 3) if size else 0
        
        is_active = "✅ " if name == active_model else ""
        text += f"{is_active}<code>{name}</code>"
        if size_gb > 0:
            text += f" ({size_gb:.1f} GB)"
        text += "\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_models_keyboard())
    await callback.answer()


@router.callback_query(F.data == "ai_admin_select_model", IsAdminFilter())
async def callback_ai_admin_select_model(callback: CallbackQuery, db: Database):
    """Выбор активной модели."""
    service = get_service(db)
    models = await service.list_models()
    active_model = await service.get_active_model()
    
    if not models:
        await callback.answer("❌ Нет установленных моделей", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    
    for model in models[:15]:
        name = model.get("name", "unknown")
        prefix = "✅ " if name == active_model else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{name}",
                callback_data=f"ai_admin_set_active:{name}"
            )
        )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="ai_admin_models"))
    
    await callback.message.edit_text(
        "✅ <b>Выбор активной модели</b>\n\n"
        f"Текущая: <code>{active_model}</code>\n\n"
        "Выберите модель для всех пользователей:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai_admin_set_active:"), IsAdminFilter())
async def callback_ai_admin_set_active(callback: CallbackQuery, db: Database, user: User):
    """Установить активную модель."""
    model = callback.data.split(":", 1)[1]
    
    service = get_service(db)
    success = await service.set_active_model(model)
    
    if success:
        logger.info(f"Admin {user.telegram_id} set active model to: {model}")
        await callback.answer(f"✅ Модель {model} установлена как активная", show_alert=True)
        
        await callback.message.edit_text(
            f"✅ <b>Модель изменена</b>\n\n"
            f"Активная модель: <code>{model}</code>\n\n"
            f"Все сессии пользователей очищены.",
            reply_markup=get_admin_models_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка установки модели", show_alert=True)


@router.callback_query(F.data == "ai_admin_pull_model", IsAdminFilter())
async def callback_ai_admin_pull_model(callback: CallbackQuery, state: FSMContext):
    """Начать загрузку модели."""
    await state.set_state(AIStates.selecting_model)
    
    await callback.message.edit_text(
        "📥 <b>Загрузка модели</b>\n\n"
        "Введите название модели для загрузки.\n\n"
        "Примеры:\n"
        "• <code>llama3.2</code>\n"
        "• <code>llama3.1:8b</code>\n"
        "• <code>mistral</code>\n"
        "• <code>phi3</code>\n"
        "• <code>codellama</code>\n\n"
        "Список моделей: https://ollama.com/library",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AIStates.selecting_model, IsAdminFilter())
async def process_pull_model(message: Message, state: FSMContext, db: Database, user: User):
    """Обработка загрузки модели."""
    model_name = message.text.strip()
    
    if not model_name:
        await message.answer("❌ Введите название модели.")
        return
    
    await state.clear()
    
    service = get_service(db)
    
    status_message = await message.answer(
        f"📥 <b>Загрузка модели</b>\n\n"
        f"Модель: <code>{model_name}</code>\n"
        f"Статус: начало загрузки..."
    )
    
    last_update = 0
    last_status = ""
    
    async for chunk in service.pull_model(model_name):
        if "error" in chunk:
            await status_message.edit_text(
                f"❌ <b>Ошибка загрузки</b>\n\n"
                f"Модель: <code>{model_name}</code>\n"
                f"Ошибка: {chunk['error']}",
                reply_markup=get_admin_models_keyboard()
            )
            return
        
        status = chunk.get("status", "")
        
        # Обновляем сообщение не чаще раза в 2 секунды
        import time
        current_time = time.time()
        
        if status != last_status and current_time - last_update > 2:
            progress = ""
            if "completed" in chunk and "total" in chunk:
                completed = chunk["completed"]
                total = chunk["total"]
                if total > 0:
                    percent = (completed / total) * 100
                    progress = f"\nПрогресс: {percent:.1f}%"
            
            try:
                await status_message.edit_text(
                    f"📥 <b>Загрузка модели</b>\n\n"
                    f"Модель: <code>{model_name}</code>\n"
                    f"Статус: {status}{progress}"
                )
                last_update = current_time
                last_status = status
            except Exception:
                pass
        
        if status == "success":
            logger.info(f"Admin {user.telegram_id} pulled model: {model_name}")
            await status_message.edit_text(
                f"✅ <b>Модель загружена</b>\n\n"
                f"Модель: <code>{model_name}</code>\n\n"
                f"Теперь вы можете установить её как активную.",
                reply_markup=get_admin_models_keyboard()
            )
            return
    
    await status_message.edit_text(
        f"✅ <b>Загрузка завершена</b>\n\n"
        f"Модель: <code>{model_name}</code>",
        reply_markup=get_admin_models_keyboard()
    )


@router.callback_query(F.data == "ai_admin_delete_model", IsAdminFilter())
async def callback_ai_admin_delete_model(callback: CallbackQuery, db: Database):
    """Выбор модели для удаления."""
    service = get_service(db)
    models = await service.list_models()
    active_model = await service.get_active_model()
    
    if not models:
        await callback.answer("❌ Нет установленных моделей", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    
    for model in models:
        name = model.get("name", "unknown")
        # Нельзя удалить активную модель
        if name == active_model:
            builder.row(
                InlineKeyboardButton(
                    text=f"🔒 {name} (активная)",
                    callback_data="ai_noop"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"🗑 {name}",
                    callback_data=f"ai_admin_confirm_delete:{name}"
                )
            )
    
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="ai_admin_models"))
    
    await callback.message.edit_text(
        "🗑 <b>Удаление модели</b>\n\n"
        "Выберите модель для удаления:\n\n"
        "<i>Активную модель удалить нельзя.</i>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai_admin_confirm_delete:"), IsAdminFilter())
async def callback_ai_admin_confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления модели."""
    model = callback.data.split(":", 1)[1]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"ai_admin_do_delete:{model}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="ai_admin_delete_model")
    )
    
    await callback.message.edit_text(
        f"🗑 <b>Подтверждение удаления</b>\n\n"
        f"Вы уверены, что хотите удалить модель?\n\n"
        f"Модель: <code>{model}</code>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai_admin_do_delete:"), IsAdminFilter())
async def callback_ai_admin_do_delete(callback: CallbackQuery, db: Database, user: User):
    """Выполнение удаления модели."""
    model = callback.data.split(":", 1)[1]
    
    service = get_service(db)
    success = await service.delete_model(model)
    
    if success:
        logger.info(f"Admin {user.telegram_id} deleted model: {model}")
        await callback.answer(f"✅ Модель {model} удалена", show_alert=True)
        
        await callback.message.edit_text(
            f"✅ <b>Модель удалена</b>\n\n"
            f"Модель <code>{model}</code> успешно удалена.",
            reply_markup=get_admin_models_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка удаления модели", show_alert=True)


@router.callback_query(F.data == "ai_noop")
async def callback_ai_noop(callback: CallbackQuery):
    """Пустой callback."""
    await callback.answer()


# ============================================================================
# КОМАНДЫ АДМИНИСТРАТОРА (текстовые)
# ============================================================================

@router.message(Command("ai_models"), IsAdminFilter())
async def cmd_ai_models_admin(message: Message, db: Database):
    """Показать модели (для админов)."""
    service = get_service(db)
    models = await service.list_models()
    active_model = await service.get_active_model()
    
    if not models:
        await message.answer(
            "📋 <b>Модели</b>\n\n"
            "Нет установленных моделей.\n"
            "Используйте /ai для управления."
        )
        return
    
    text = f"📋 <b>Установленные модели</b>\n\n"
    text += f"🟢 Активная: <code>{active_model}</code>\n\n"
    
    for model in models:
        name = model.get("name", "unknown")
        size = model.get("size", 0)
        size_gb = size / (1024 ** 3) if size else 0
        
        is_active = "✅ " if name == active_model else "  "
        text += f"{is_active}<code>{name}</code>"
        if size_gb > 0:
            text += f" ({size_gb:.1f} GB)"
        text += "\n"
    
    text += "\nИспользуйте /ai → Управление моделями"
    
    await message.answer(text)


@router.message(Command("ai_models"))
async def cmd_ai_models_user(message: Message, db: Database):
    """Показать активную модель (для пользователей)."""
    service = get_service(db)
    active_model = await service.get_active_model()
    
    await message.answer(
        f"🤖 <b>AI Ассистент</b>\n\n"
        f"Активная модель: <code>{active_model}</code>\n\n"
        f"Используйте /ai для начала работы."
    )