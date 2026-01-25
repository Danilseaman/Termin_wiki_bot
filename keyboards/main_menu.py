from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню с инлайн-кнопками"""
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="🔍 Термин", callback_data="term_search"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
        [
            InlineKeyboardButton(text="📞 Контакты", callback_data="contacts"),
            InlineKeyboardButton(text="📝 FAQ", callback_data="faq"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Назад'"""
    keyboard = [[
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def term_result_keyboard(wikipedia_url: str = None) -> InlineKeyboardMarkup:
    """Клавиатура для результата поиска термина"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]

    if wikipedia_url:
        keyboard.insert(0, [
            InlineKeyboardButton(
                text="📖 Полная статья",
                url=wikipedia_url
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)