"""
Пример создания пользовательского обработчика.

Этот модуль демонстрирует, как создавать собственные обработчики для
расширения функциональности бота. Каждый обработчик должен быть
оформлен как Router и зарегистрирован в bot/handlers/__init__.py.

Структура обработчика:
1. Создание Router с уникальным именем
2. Определение обработчиков команд, сообщений и callback
3. Использование состояний FSM при необходимости
4. Работа с сервисами и репозиториями через dependency injection

Example:
    Для добавления нового обработчика:
    
    1. Создайте файл в bot/handlers/ (например, my_handler.py)
    2. Определите Router и обработчики
    3. Зарегистрируйте в bot/handlers/__init__.py:
       
       from .my_handler import router as my_router
       
       def setup_routers(dp: Dispatcher):
           dp.include_router(my_router)
           ...

Note:
    - Все обработчики должны быть асинхронными
    - Используйте типизацию для параметров
    - Добавляйте docstring к каждому обработчику
    - Группируйте связанные обработчики в один Router
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import Database
from database.repositories.users import User
from services.example_service import ExampleService
from bot.keyboards.builders import get_main_menu_keyboard, get_cancel_keyboard


# ============================================================================
# 1. ОПРЕДЕЛЕНИЕ РОУТЕРА
# ============================================================================

# Создаём роутер с уникальным именем для логирования и отладки
router = Router(name="example")


# ============================================================================
# 2. ОПРЕДЕЛЕНИЕ СОСТОЯНИЙ FSM (если нужны диалоги)
# ============================================================================

class ExampleStates(StatesGroup):
    """
    Состояния для примера диалога.
    
    Каждое состояние представляет шаг в диалоге с пользователем.
    Названия состояний должны быть описательными.
    """
    waiting_for_input = State()
    waiting_for_confirmation = State()


# ============================================================================
# 3. ОБРАБОТЧИКИ КОМАНД
# ============================================================================

@router.message(Command("example"))
async def cmd_example(message: Message, user: User, db: Database):
    """
    Обработчик команды /example.
    
    Демонстрирует базовую структуру обработчика команды.
    
    Args:
        message: Входящее сообщение от пользователя
        user: Объект пользователя из БД (добавляется middleware)
        db: Экземпляр базы данных (добавляется middleware)
    
    Note:
        Параметры user и db автоматически добавляются AuthMiddleware.
        Вы можете использовать их напрямую в обработчике.
    """
    # Пример использования сервиса
    service = ExampleService(db)
    stats = await service.get_user_statistics(user.id)
    
    await message.answer(
        f"👋 Привет, <b>{user.full_name or 'пользователь'}</b>!\n\n"
        f"Это пример обработчика.\n\n"
        f"<b>Ваша статистика:</b>\n"
        f"• ID: {stats.get('user_id')}\n"
        f"• Часовой пояс: {stats.get('timezone')}\n"
        f"• Зарегистрирован: {stats.get('registered_at')}"
    )


# ============================================================================
# 4. ОБРАБОТЧИКИ С FSM (диалоги)
# ============================================================================

@router.message(Command("example_dialog"))
async def cmd_example_dialog(message: Message, state: FSMContext):
    """
    Начало примера диалога с использованием FSM.
    
    FSM (Finite State Machine) позволяет создавать многошаговые диалоги,
    где бот запоминает текущий шаг и ожидает определённый ввод.
    
    Args:
        message: Входящее сообщение
        state: Контекст FSM для управления состоянием
    """
    # Устанавливаем состояние ожидания ввода
    await state.set_state(ExampleStates.waiting_for_input)
    
    # Можно сохранить данные в состоянии
    await state.update_data(started_at=message.date.isoformat())
    
    await message.answer(
        "📝 <b>Пример диалога</b>\n\n"
        "Введите любой текст для обработки:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ExampleStates.waiting_for_input)
async def process_example_input(message: Message, state: FSMContext, db: Database):
    """
    Обработка ввода пользователя в состоянии waiting_for_input.
    
    Этот обработчик вызывается только когда пользователь находится
    в состоянии ExampleStates.waiting_for_input.
    
    Args:
        message: Сообщение с вводом пользователя
        state: Контекст FSM
        db: База данных
    """
    # Получаем ранее сохранённые данные
    data = await state.get_data()
    
    # Используем сервис для обработки
    service = ExampleService(db)
    result = await service.process_data(message.text)
    
    if result.success:
        # Очищаем состояние - диалог завершён
        await state.clear()
        
        await message.answer(
            f"✅ <b>Результат обработки</b>\n\n"
            f"{result.message}\n\n"
            f"<i>Диалог начат: {data.get('started_at')}</i>",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Оставляем в том же состоянии для повторного ввода
        await message.answer(
            f"❌ {result.message}\n\n"
            "Попробуйте ещё раз:",
            reply_markup=get_cancel_keyboard()
        )


# ============================================================================
# 5. ОБРАБОТЧИКИ CALLBACK QUERY
# ============================================================================

@router.callback_query(F.data == "example_action")
async def callback_example_action(callback: CallbackQuery, user: User):
    """
    Обработчик callback query.
    
    Вызывается при нажатии inline-кнопки с callback_data="example_action".
    
    Args:
        callback: Объект callback query
        user: Пользователь из БД
        
    Note:
        Всегда вызывайте callback.answer() в конце обработчика,
        иначе пользователь увидит "часики" на кнопке.
    """
    await callback.message.edit_text(
        f"🎯 Вы нажали на кнопку!\n\n"
        f"Пользователь: {user.username or user.full_name}",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Обязательно отвечаем на callback
    await callback.answer("Действие выполнено!")


@router.callback_query(F.data.startswith("example_item:"))
async def callback_example_item(callback: CallbackQuery):
    """
    Обработчик callback с параметром.
    
    Демонстрирует извлечение параметра из callback_data.
    Формат: "example_item:123" где 123 - ID элемента.
    
    Args:
        callback: Объект callback query
    """
    # Извлекаем ID из callback_data
    item_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        f"📦 Вы выбрали элемент с ID: {item_id}",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


# ============================================================================
# 6. ОБРАБОТЧИКИ ФАЙЛОВ (опционально)
# ============================================================================

@router.message(F.document)
async def handle_document(message: Message, user: User, db: Database):
    """
    Обработчик получения документа.
    
    Этот обработчик будет вызван при отправке любого документа боту.
    
    Args:
        message: Сообщение с документом
        user: Пользователь из БД
        db: База данных
        
    Note:
        Для сохранения файлов используйте FileManagerService.
        Этот обработчик - только пример, в production коде
        добавьте проверки размера файла, типа и т.д.
    """
    document = message.document
    
    # Пример: просто отвечаем информацией о файле
    await message.answer(
        f"📎 <b>Получен файл</b>\n\n"
        f"Имя: {document.file_name}\n"
        f"Размер: {document.file_size} байт\n"
        f"MIME: {document.mime_type}\n\n"
        f"<i>Для сохранения файла используйте FileManagerService</i>"
    )


# ============================================================================
# 7. ФИЛЬТРЫ (опционально)
# ============================================================================

# Можно добавить фильтр ко всему роутеру:
# router.message.filter(IsAdminFilter())  # Только для админов

# Или к конкретному обработчику:
# @router.message(Command("admin_example"), IsAdminFilter())
# async def admin_only_handler(message: Message):
#     pass