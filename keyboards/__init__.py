from .main_menu import main_menu, back_keyboard, term_result_keyboard
from .inline_navigation import settings_menu, pagination_menu
from .registration import (
    registration_keyboard,
    profile_keyboard,
    edit_profile_keyboard,
    back_to_profile_keyboard,  # Добавляем
    skip_keyboard
)

__all__ = [
    'main_menu',
    'back_keyboard',
    'term_result_keyboard',
    'settings_menu',
    'pagination_menu',
    'registration_keyboard',
    'profile_keyboard',
    'edit_profile_keyboard',
    'back_to_profile_keyboard',  # Добавляем
    'skip_keyboard'
]