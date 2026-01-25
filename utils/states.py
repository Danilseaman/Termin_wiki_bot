from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()
    waiting_for_age = State()

class SearchStates(StatesGroup):
    """Состояния для поиска"""
    waiting_for_term = State()

class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    editing_first_name = State()
    editing_last_name = State()
    editing_email = State()
    editing_age = State()