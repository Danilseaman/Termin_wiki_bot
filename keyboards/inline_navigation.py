from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = [
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications")],
        [InlineKeyboardButton(text="🌍 Язык", callback_data="language")],
        [InlineKeyboardButton(text="🎨 Тема", callback_data="theme")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def pagination_menu(page: int = 1) -> InlineKeyboardMarkup:
    """Меню с пагинацией (пример)"""
    items_per_page = 5
    total_items = 15
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # Эмуляция данных
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    buttons = []
    for i in range(start_idx + 1, end_idx + 1):
        buttons.append([InlineKeyboardButton(
            text=f"Элемент {i}",
            callback_data=f"item_{i}"
        )])

    # Кнопки пагинации
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"page_{page - 1}"
        ))

    pagination_buttons.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="current_page"
    ))

    if page < total_pages:
        pagination_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"page_{page + 1}"
        ))

    buttons.append(pagination_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)