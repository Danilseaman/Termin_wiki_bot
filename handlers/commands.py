from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from keyboards import main_menu, back_keyboard, back_to_profile_keyboard, profile_keyboard
from utils import (
    get_welcome_message,
    get_help_message,
    format_user_profile,
    RegistrationStates,
)
from database import db
from config import config

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработка команды /start"""
    # Создаем или получаем пользователя
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    # Проверяем, зарегистрирован ли пользователь
    if user.is_registered:
        # Пользователь уже зарегистрирован
        username = message.from_user.username or message.from_user.first_name
        welcome_text = get_welcome_message(username)

        await message.answer(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    else:
        # Начинаем процесс регистрации
        await message.answer(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Для полноценной работы с ботом нужно пройти быструю регистрацию.\n\n"
            "Пожалуйста, введите ваше <b>имя</b>:",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove() # Cкрываем клавиатуру
        )
        await state.set_state(RegistrationStates.waiting_for_first_name)


@router.message(Command("menu"))
async def command_menu_handler(message: Message) -> None:
    """Обработка команды /menu"""
    # Проверяем регистрацию
    user = await db.get_user_profile(message.from_user.id)

    if user and user.is_registered:
        from utils import get_main_menu_text

        await message.answer(
            get_main_menu_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Обработка команды /help"""
    # Проверяем регистрацию
    user = await db.get_user_profile(message.from_user.id)

    if user and user.is_registered:
        await message.answer(
            get_help_message(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )
    else:
        await message.answer(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("profile"))
async def command_profile_handler(message: Message) -> None:
    """Обработка команды /profile - просмотр профиля"""
    user = await db.get_user_profile(message.from_user.id)

    if user and user.is_registered:
        profile_text = format_user_profile(user)

        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    else:
        await message.answer(
            "⚠️ <b>Профиль не найден!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("history"))
async def command_history_handler(message: Message) -> None:
    """Обработка команды /history - история поиска"""
    user = await db.get_user_profile(message.from_user.id)

    if user and user.is_registered:
        history = await db.get_user_search_history(message.from_user.id, limit=5)

        if history:
            from utils import format_search_history_item

            history_text = "<b>📜 История ваших поисков:</b>\n\n"
            for i, item in enumerate(history, 1):
                history_text += f"<b>{i}.</b>\n{format_search_history_item(item)}\n\n"

            await message.answer(
                history_text,
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_profile_keyboard()  # Меняем на back_to_profile
            )
        else:
            await message.answer(
                "📭 <b>История поиска пуста</b>\n\n"
                "Вы еще не выполняли поиск терминов.",
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_profile_keyboard()  # Меняем на back_to_profile
            )
    else:
        await message.answer(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("stats"))
async def command_stats_handler(message: Message) -> None:
    """Обработка команды /stats - статистика пользователя"""
    user = await db.get_user_profile(message.from_user.id)

    if user and user.is_registered:
        user_stats = await db.get_user_stats(message.from_user.id)

        if user_stats:
            from utils import bold, code

            stats_text = f"{bold('📊 Ваша статистика:')}\n\n"
            stats_text += f"{bold('👤 Пользователь:')} {user.first_name or 'Не указано'}\n"
            stats_text += f"{bold('🔍 Всего поисков:')} {user_stats['total_searches']}\n"
            stats_text += f"{bold('✅ Успешных:')} {user_stats['successful_searches']}\n"

            # Даты уже отформатированы в базе данных
            if user_stats.get('first_search'):
                stats_text += f"{bold('📅 Первый поиск:')} {user_stats['first_search']}\n"

            if user_stats.get('last_search'):
                stats_text += f"{bold('⏰ Последний поиск:')} {user_stats['last_search']}\n"

            if user_stats.get('popular_terms'):
                stats_text += f"\n{bold('🏆 Ваши популярные запросы:')}\n"
                for i, (term, count) in enumerate(user_stats['popular_terms'], 1):
                    stats_text += f"{i}. {code(term)} — {count}\n"

            await message.answer(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_profile_keyboard()
            )
    else:
        await message.answer(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("admin_stats"))
async def command_admin_stats_handler(message: Message) -> None:
    """Обработка команды /admin_stats - статистика бота (только для админов)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer(
            "⛔ <b>Доступ запрещен!</b>\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode=ParseMode.HTML
        )
        return

    stats = await db.get_bot_stats()
    from utils import format_bot_stats

    await message.answer(
        format_bot_stats(stats),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )


@router.message(Command("admin_users"))
async def command_admin_users_handler(message: Message) -> None:
    """Обработка команды /admin_users - просмотр всех пользователей (админы)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer(
            "⛔ <b>Доступ запрещен!</b>\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode=ParseMode.HTML
        )
        return

    # Проверяем наличие аргументов
    args = message.text.split()
    limit = 20  # По умолчанию показываем 20 пользователей

    if len(args) > 1:
        try:
            limit = int(args[1])
            limit = min(limit, 100)  # Ограничиваем максимум 100 пользователей
        except ValueError:
            await message.answer(
                "❌ <b>Неверный аргумент.</b>\n\n"
                "Используйте: <code>/admin_users [количество]</code>\n"
                "где количество - число от 1 до 100.",
                parse_mode=ParseMode.HTML
            )
            return

    # Получаем всех пользователей
    users = await db.get_all_users(limit=limit)

    if not users:
        await message.answer(
            "📭 <b>Нет зарегистрированных пользователей.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    from utils import format_users_list_for_admin
    users_list = format_users_list_for_admin(users)

    # Добавляем общую статистику
    stats = await db.get_bot_stats()
    users_list += (
        f"\n\n<b>📊 Общая статистика:</b>\n"
        f"• Всего пользователей: {stats.total_users}\n"
        f"• Активных (30 дней): {stats.active_users}\n"
        f"• Всего поисков: {stats.total_searches}"
    )

    await message.answer(
        users_list,
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )


@router.message(Command("admin_delete_user"))
async def command_admin_delete_user_handler(message: Message) -> None:
    """Обработка команды /admin_delete_user - удаление пользователя (админы)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer(
            "⛔ <b>Доступ запрещен!</b>\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode=ParseMode.HTML
        )
        return

    # Проверяем, указан ли user_id в команде
    args = message.text.split()
    if len(args) < 2:
        # Если user_id не указан, показываем список пользователей
        users = await db.get_all_users(limit=10)

        if not users:
            await message.answer(
                "📭 <b>Нет зарегистрированных пользователей.</b>",
                parse_mode=ParseMode.HTML
            )
            return

        from utils import format_users_list_for_admin
        users_list = format_users_list_for_admin(users)

        users_list += (
            f"\n\n<b>Для удаления пользователя используйте:</b>\n"
            f"<code>/admin_delete_user USER_ID</code>\n\n"
            f"<i>Пример: /admin_delete_user 123456789</i>"
        )

        await message.answer(
            users_list,
            parse_mode=ParseMode.HTML
        )
        return

    # Пытаемся получить user_id из аргументов
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат ID пользователя.</b>\n\n"
            "Используйте: <code>/admin_delete_user USER_ID</code>\n"
            "где USER_ID - числовой ID пользователя в Telegram.",
            parse_mode=ParseMode.HTML
        )
        return

    # Проверяем, не пытается ли администратор удалить свои данные
    if target_user_id == message.from_user.id:
        await message.answer(
            "⚠️ <b>Вы не можете удалить свой собственный профиль через эту команду.</b>\n\n"
            "Обратитесь к другому администратору для удаления вашего профиля.",
            parse_mode=ParseMode.HTML
        )
        return

    # Получаем информацию о пользователе
    target_user = await db.get_user_profile(target_user_id)

    if not target_user:
        await message.answer(
            f"❌ <b>Пользователь с ID <code>{target_user_id}</code> не найден.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    # Создаем клавиатуру для подтверждения удаления
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, удалить пользователя",
                callback_data=f"admin_confirm_delete:{target_user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin_cancel_delete"
            )
        ]
    ])

    await message.answer(
        f"⚠️ <b>Удаление пользователя</b>\n\n"
        f"Вы собираетесь удалить пользователя:\n"
        f"• <b>ID:</b> <code>{target_user.telegram_id}</code>\n"
        f"• <b>Имя:</b> {target_user.first_name or 'Не указано'}\n"
        f"• <b>Фамилия:</b> {target_user.last_name or 'Не указана'}\n"
        f"• <b>Username:</b> @{target_user.username or 'нет'}\n"
        f"• <b>Email:</b> {target_user.email or 'Не указан'}\n"
        f"• <b>Поисков:</b> {target_user.search_count}\n"
        f"• <b>Дата регистрации:</b> {target_user.registration_date.strftime('%d.%m.%Y %H:%M') if target_user.registration_date else 'Не указана'}\n\n"
        f"<b>Будут удалены:</b>\n"
        f"• Профиль пользователя\n"
        f"• Вся история поисков ({target_user.search_count} записей)\n\n"
        f"<b>Это действие нельзя отменить!</b>\n\n"
        f"Подтвердите удаление пользователя:",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )