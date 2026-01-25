from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def registration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для регистрации"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Заполнить позже", callback_data="skip_registration")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_registration")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для профиля"""
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
            InlineKeyboardButton(text="📜 История", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="user_stats"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def edit_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для редактирования профиля"""
    keyboard = [
        [InlineKeyboardButton(text="👤 Имя", callback_data="edit_first_name")],
        [InlineKeyboardButton(text="👤 Фамилия", callback_data="edit_last_name")],
        [InlineKeyboardButton(text="📧 Email", callback_data="edit_email")],
        [InlineKeyboardButton(text="🎂 Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="🔙 Назад к профилю", callback_data="back_to_profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Назад к профилю'"""
    keyboard = [[
        InlineKeyboardButton(text="🔙 Назад к профилю", callback_data="back_to_profile")
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой 'Пропустить'"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )