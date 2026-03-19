"""
Состояния FSM для диалогов.
"""

from aiogram.fsm.state import State, StatesGroup



class NoteStates(StatesGroup):
    """Состояния для работы с заметками."""
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_edit_title = State()
    waiting_for_edit_content = State()
    waiting_for_template_select = State()


class ReminderStates(StatesGroup):
    """Состояния для работы с напоминаниями."""
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_datetime = State()
    waiting_for_repeat_interval = State()
    waiting_for_edit_title = State()
    waiting_for_edit_content = State()  # <-- Добавлено
    waiting_for_edit_datetime = State()
    waiting_for_template_select = State()


class TemplateStates(StatesGroup):
    """Состояния для работы с шаблонами."""
    waiting_for_name = State()
    waiting_for_title_template = State()
    waiting_for_content_template = State()
    waiting_for_type_select = State()


class TimezoneStates(StatesGroup):
    """Состояния для настройки часового пояса."""
    waiting_for_timezone = State()


class AdminStates(StatesGroup):
    """Состояния для административных функций."""
    waiting_for_user_id = State()
    waiting_for_script_select = State()
    confirm_restart = State()
    
# ... существующие классы ...

class AIStates(StatesGroup):
class AIStates(StatesGroup):
    """Состояния для AI чата."""
    chatting = State()
    waiting_for_prompt = State()
    selecting_model = State()  # Для админа - ввод названия модели
    selecting_mode = State()