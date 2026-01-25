"""
Обработчики регистрации и профиля пользователя
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from keyboards import main_menu, profile_keyboard, edit_profile_keyboard, skip_keyboard
from utils import (
    RegistrationStates,
    ProfileStates,
    format_user_profile,
    validate_email,
    validate_age
)
from database import db
from config import config

router = Router()

# ---------- Обработчики регистрации ----------
@router.message(StateFilter(RegistrationStates.waiting_for_first_name))
async def process_first_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода имени"""
    if message.text.lower() == "пропустить":
        await state.update_data(first_name=None)
        await message.answer(
            "Пожалуйста, введите вашу <b>фамилию</b> (или нажмите 'Пропустить'):",
            parse_mode=ParseMode.HTML,
            reply_markup=skip_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_last_name)
        return

    if len(message.text.strip()) < 2:
        await message.answer(
            "❌ Имя должно содержать не менее 2 символов. Попробуйте еще раз:",
            parse_mode=ParseMode.HTML
        )
        return

    await state.update_data(first_name=message.text.strip())
    await message.answer(
        "Пожалуйста, введите вашу <b>фамилию</b> (или нажмите 'Пропустить'):",
        parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_last_name)

@router.message(StateFilter(RegistrationStates.waiting_for_last_name))
async def process_last_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода фамилии"""
    if message.text.lower() == "пропустить":
        await state.update_data(last_name=None)
        await message.answer(
            "Пожалуйста, введите ваш <b>email</b> (или нажмите 'Пропустить'):",
            parse_mode=ParseMode.HTML,
            reply_markup=skip_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_email)
        return

    await state.update_data(last_name=message.text.strip())
    await message.answer(
        "Пожалуйста, введите ваш <b>email</b> (или нажмите 'Пропустить'):",
        parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_email)

@router.message(StateFilter(RegistrationStates.waiting_for_email))
async def process_email(message: Message, state: FSMContext) -> None:
    """Обработка ввода email"""
    if message.text.lower() == "пропустить":
        await state.update_data(email=None)
        await message.answer(
            "Пожалуйста, введите ваш <b>возраст</b> (или нажмите 'Пропустить'):",
            parse_mode=ParseMode.HTML,
            reply_markup=skip_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_age)
        return

    email = message.text.strip()
    if not validate_email(email):
        await message.answer(
            "❌ Неверный формат email. Пожалуйста, введите корректный email:",
            parse_mode=ParseMode.HTML,
            reply_markup=skip_keyboard()
        )
        return

    await state.update_data(email=email)
    await message.answer(
        "Пожалуйста, введите ваш <b>возраст</b> (или нажмите 'Пропустить'):",
        parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(StateFilter(RegistrationStates.waiting_for_age))
async def process_age(message: Message, state: FSMContext) -> None:
    """Обработка ввода возраста и завершение регистрации"""
    age = None
    if message.text.lower() != "пропустить":
        age = validate_age(message.text.strip())
        if age is None:
            await message.answer(
                "❌ Возраст должен быть числом от 1 до 120. Попробуйте еще раз:",
                parse_mode=ParseMode.HTML,
                reply_markup=skip_keyboard()
            )
            return

    user_data = await state.get_data()

    # Сохраняем профиль в базу данных
    success = await db.update_user_profile(
        telegram_id=message.from_user.id,
        email=user_data.get('email'),
        age=age,
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name')
    )

    if success:
        user = await db.get_user_profile(message.from_user.id)

        await message.answer(
            "✅ <b>Регистрация завершена!</b>\n\n"
            "Теперь вы можете пользоваться всеми функциями бота.",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove()
        )

        # Показываем профиль
        profile_text = format_user_profile(user)
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )

        # Показываем главное меню
        from utils import get_main_menu_text
        await message.answer(
            get_main_menu_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при сохранении данных.</b>\n\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой.",
            parse_mode=ParseMode.HTML
        )

    await state.clear()

# ---------- Обработчики редактирования профиля ----------
@router.callback_query(F.data == "edit_profile")
async def edit_profile_handler(callback: CallbackQuery) -> None:
    """Обработка кнопки редактирования профиля"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование профиля</b>\n\n"
        "Выберите, что хотите изменить:",
        parse_mode=ParseMode.HTML,
        reply_markup=edit_profile_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "edit_first_name")
async def edit_first_name_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование имени"""
    await callback.message.edit_text(
        "Введите ваше новое <b>имя</b>:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ProfileStates.editing_first_name)
    await callback.answer()

@router.callback_query(F.data == "edit_last_name")
async def edit_last_name_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование фамилии"""
    await callback.message.edit_text(
        "Введите вашу новую <b>фамилию</b>:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ProfileStates.editing_last_name)
    await callback.answer()

@router.callback_query(F.data == "edit_email")
async def edit_email_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование email"""
    await callback.message.edit_text(
        "Введите ваш новый <b>email</b>:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ProfileStates.editing_email)
    await callback.answer()

@router.callback_query(F.data == "edit_age")
async def edit_age_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование возраста"""
    await callback.message.edit_text(
        "Введите ваш новый <b>возраст</b>:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ProfileStates.editing_age)
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат к профилю"""
    await state.clear()
    user = await db.get_user_profile(callback.from_user.id)

    if user:
        profile_text = format_user_profile(user)
        await callback.message.edit_text(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    await callback.answer()

# ---------- Обработчики сохранения изменений профиля ----------
@router.message(StateFilter(ProfileStates.editing_first_name))
async def save_first_name(message: Message, state: FSMContext) -> None:
    """Сохранение нового имени"""
    if len(message.text.strip()) < 2:
        await message.answer(
            "❌ Имя должно содержать не менее 2 символов. Попробуйте еще раз:",
            parse_mode=ParseMode.HTML
        )
        return

    success = await db.update_user_profile(
        telegram_id=message.from_user.id,
        first_name=message.text.strip()
    )

    if success:
        user = await db.get_user_profile(message.from_user.id)
        profile_text = format_user_profile(user)

        await message.answer(
            "✅ <b>Имя успешно обновлено!</b>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при обновлении имени.</b>",
            parse_mode=ParseMode.HTML
        )

    await state.clear()

@router.message(StateFilter(ProfileStates.editing_last_name))
async def save_last_name(message: Message, state: FSMContext) -> None:
    """Сохранение новой фамилии"""
    success = await db.update_user_profile(
        telegram_id=message.from_user.id,
        last_name=message.text.strip()
    )

    if success:
        user = await db.get_user_profile(message.from_user.id)
        profile_text = format_user_profile(user)

        await message.answer(
            "✅ <b>Фамилия успешно обновлена!</b>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при обновлении фамилии.</b>",
            parse_mode=ParseMode.HTML
        )

    await state.clear()

@router.message(StateFilter(ProfileStates.editing_email))
async def save_email(message: Message, state: FSMContext) -> None:
    """Сохранение нового email"""
    email = message.text.strip()
    if not validate_email(email):
        await message.answer(
            "❌ Неверный формат email. Пожалуйста, введите корректный email:",
            parse_mode=ParseMode.HTML
        )
        return

    success = await db.update_user_profile(
        telegram_id=message.from_user.id,
        email=email
    )

    if success:
        user = await db.get_user_profile(message.from_user.id)
        profile_text = format_user_profile(user)

        await message.answer(
            "✅ <b>Email успешно обновлен!</b>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при обновлении email.</b>",
            parse_mode=ParseMode.HTML
        )

    await state.clear()

@router.message(StateFilter(ProfileStates.editing_age))
async def save_age(message: Message, state: FSMContext) -> None:
    """Сохранение нового возраста"""
    age = validate_age(message.text.strip())
    if age is None:
        await message.answer(
            "❌ Возраст должен быть числом от 1 до 120. Попробуйте еще раз:",
            parse_mode=ParseMode.HTML
        )
        return

    success = await db.update_user_profile(
        telegram_id=message.from_user.id,
        age=age
    )

    if success:
        user = await db.get_user_profile(message.from_user.id)
        profile_text = format_user_profile(user)

        await message.answer(
            "✅ <b>Возраст успешно обновлен!</b>",
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при обновлении возраста.</b>",
            parse_mode=ParseMode.HTML
        )

    await state.clear()

# ---------- Обработчики отмены регистрации ----------
@router.callback_query(F.data == "skip_registration")
async def skip_registration_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропуск регистрации"""
    from utils import get_main_menu_text

    await callback.message.edit_text(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Вы можете заполнить профиль позже в разделе профиля.\n\n"
        "Доступ к поиску терминов ограничен до завершения регистрации.",
        parse_mode=ParseMode.HTML
    )

    await callback.message.answer(
        get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_registration")
async def cancel_registration_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена регистрации"""
    await callback.message.edit_text(
        "❌ <b>Регистрация отменена.</b>\n\n"
        "Вы можете начать регистрацию позже с помощью команды /start",
        parse_mode=ParseMode.HTML
    )
    await state.clear()
    await callback.answer()

# ---------- Обработчики административного удаления пользователей ----------
@router.callback_query(F.data.startswith("admin_confirm_delete:"))
async def admin_confirm_delete_handler(callback: CallbackQuery) -> None:
    """Подтверждение административного удаления пользователя"""
    # Проверяем права администратора
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        return

    # Извлекаем user_id из callback_data
    try:
        target_user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.message.edit_text(
            "❌ <b>Ошибка при обработке запроса.</b>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return

    # Выполняем удаление данных
    success = await db.delete_user_data(target_user_id)

    if success:
        # Получаем статистику для обновления информации
        stats = await db.get_bot_stats()

        await callback.message.edit_text(
            f"✅ <b>Пользователь <code>{target_user_id}</code> успешно удален.</b>\n\n"
            f"<b>Обновленная статистика:</b>\n"
            f"• Пользователей в системе: {stats.total_users}\n"
            f"• Всего поисков: {stats.total_searches}",
            parse_mode=ParseMode.HTML
        )

        # Пытаемся отправить уведомление пользователю (если бот не заблокирован)
        try:
            from aiogram.exceptions import TelegramBadRequest
            from utils import bold

            warning_message = (
                f"⚠️ {bold('Внимание!')}\n\n"
                f"Администратор удалил ваш профиль и все данные из системы.\n\n"
                f"Если вы хотите снова использовать бота, "
                f"используйте команду /start для новой регистрации."
            )

            # Пытаемся отправить сообщение пользователю
            # Но не падаем, если пользователь заблокировал бота
            await callback.bot.send_message(
                chat_id=target_user_id,
                text=warning_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Не удалось уведомить пользователя {target_user_id}: {e}")

            await callback.message.edit_text(
                f"✅ <b>Пользователь <code>{target_user_id}</code> успешно удален.</b>\n\n"
                f"⚠️ <i>Не удалось отправить уведомление пользователю (возможно, бот заблокирован).</i>",
                parse_mode=ParseMode.HTML
            )
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при удалении пользователя <code>{target_user_id}</code>.</b>\n\n"
            f"Пожалуйста, попробуйте позже или проверьте корректность ID.",
            parse_mode=ParseMode.HTML
        )

    await callback.answer()

@router.callback_query(F.data == "admin_cancel_delete")
async def admin_cancel_delete_handler(callback: CallbackQuery) -> None:
    """Отмена административного удаления пользователя"""
    # Проверяем права администратора
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        return

    await callback.message.edit_text(
        "❌ <b>Удаление пользователя отменено.</b>\n\n"
        "Данные пользователя сохранены.",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()