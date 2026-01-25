from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
import wikipedia
import asyncio

from keyboards import (
    main_menu, back_keyboard, term_result_keyboard,
    settings_menu, profile_keyboard, back_to_profile_keyboard
)

from utils import (
    get_main_menu_text,
    get_search_prompt,
    get_search_started,
    get_search_result,
    get_search_not_found,
    get_search_error,
    get_disambiguation_message,
    get_about_message,
    get_contacts_message,
    get_faq_message,
    get_settings_message,
    get_settings_option_message,
    get_cancel_search_message,
    get_empty_term_message,
    format_user_profile,
    format_search_history_item,
    SearchStates
)

from database import db

router = Router()

# Устанавливаем язык для Википедии
wikipedia.set_lang("ru")

# ---------- Обработчик поиска термина (ОБНОВЛЕН с сохранением в БД) ----------
@router.message(StateFilter(SearchStates.waiting_for_term))
async def process_term(message: Message, state: FSMContext) -> None:
    """Обработка введенного пользователем термина"""
    # Проверяем регистрацию пользователя
    user = await db.get_user_profile(message.from_user.id)

    if not user or not user.is_registered:
        await message.answer(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )
        return

    term = message.text.strip()

    if not term:
        await message.answer(
            get_empty_term_message(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )
        return

    # Отправляем сообщение о начале поиска
    search_msg = await message.answer(
        get_search_started(term),
        parse_mode=ParseMode.HTML
    )

    try:
        loop = asyncio.get_event_loop()

        # Поиск страницы в Википедии
        search_results = await loop.run_in_executor(
            None,
            lambda: wikipedia.search(term, results=3)
        )

        if not search_results:
            # Сохраняем неудачный поиск в историю
            await db.add_search_history(
                telegram_id=message.from_user.id,
                search_term=term,
                success=False
            )

            await search_msg.edit_text(
                get_search_not_found(term),
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard()
            )
            await state.clear()
            return

        # Берем первый результат
        page_title = search_results[0]

        # Получаем информацию о странице
        try:
            page = await loop.run_in_executor(
                None,
                lambda: wikipedia.page(page_title, auto_suggest=False)
            )

            summary = page.summary[:1500]
            url = page.url

            # Если summary слишком короткий
            if len(summary) < 100:
                try:
                    page_content = await loop.run_in_executor(
                        None,
                        lambda: wikipedia.page(page_title, auto_suggest=True)
                    )
                    summary = page_content.summary[:1500]
                except:
                    pass

            # Формируем ответ
            response_text = get_search_result(page_title, summary)

            # Обрезаем, если слишком длинный
            if len(response_text) > 4000:
                response_text = response_text[:4000] + "..."

            # Сохраняем успешный поиск в историю
            await db.add_search_history(
                telegram_id=message.from_user.id,
                search_term=term,
                result_title=page_title,
                result_url=url,
                success=True
            )

            await search_msg.edit_text(
                response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=term_result_keyboard(url)
            )

        except wikipedia.exceptions.DisambiguationError as e:
            # Если термин неоднозначный
            options = e.options[:5]

            # Сохраняем неудачный поиск в историю (неоднозначность)
            await db.add_search_history(
                telegram_id=message.from_user.id,
                search_term=term,
                success=False
            )

            await search_msg.edit_text(
                get_disambiguation_message(term, options),
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard()
            )

        except wikipedia.exceptions.PageError:
            # Сохраняем неудачный поиск в историю
            await db.add_search_history(
                telegram_id=message.from_user.id,
                search_term=term,
                success=False
            )

            await search_msg.edit_text(
                get_search_not_found(term),
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard()
            )

        except Exception as e:
            # Сохраняем неудачный поиск в историю
            await db.add_search_history(
                telegram_id=message.from_user.id,
                search_term=term,
                success=False
            )

            await search_msg.edit_text(
                get_search_error(term, str(e)),
                parse_mode=ParseMode.HTML,
                reply_markup=back_keyboard()
            )

    except Exception as e:
        # Сохраняем неудачный поиск в историю
        await db.add_search_history(
            telegram_id=message.from_user.id,
            search_term=term,
            success=False
        )

        await search_msg.edit_text(
            get_search_error(term, str(e)),
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )

    finally:
        await state.clear()


# ---------- Новые обработчики для профиля и истории ----------
@router.callback_query(F.data == "history")
async def history_handler(callback: CallbackQuery) -> None:
    """Обработка кнопки истории"""
    history = await db.get_user_search_history(callback.from_user.id, limit=5)

    if history:
        history_text = "<b>📜 Ваша история поисков:</b>\n\n"
        for i, item in enumerate(history, 1):
            history_text += f"<b>{i}.</b>\n{format_search_history_item(item)}\n\n"

        await callback.message.edit_text(
            history_text,
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_profile_keyboard()  # Меняем на back_to_profile
        )
    else:
        await callback.message.edit_text(
            "📭 <b>История поиска пуста</b>\n\n"
            "Вы еще не выполняли поиск терминов.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_profile_keyboard()  # Меняем на back_to_profile
        )
    await callback.answer()


@router.callback_query(F.data == "user_stats")
async def user_stats_handler(callback: CallbackQuery) -> None:
    """Обработка кнопки статистики пользователя"""
    try:
        user_stats = await db.get_user_stats(callback.from_user.id)

        if user_stats:
            from utils import bold, code

            stats_text = f"{bold('📊 Ваша статистика:')}\n\n"
            stats_text += f"{bold('👤 Пользователь:')} {user_stats['user'].first_name or 'Не указано'}\n"
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

            await callback.message.edit_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_profile_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Статистика не найдена</b>\n\n"
                "Вы еще не выполняли поиск терминов.",
                parse_mode=ParseMode.HTML,
                reply_markup=back_to_profile_keyboard()
            )
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        import traceback
        traceback.print_exc()

        await callback.message.edit_text(
            "⚠️ <b>Ошибка при получении статистики</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_profile_keyboard()
        )

    await callback.answer()


# ---------- Существующие обработчики (обновлены) ----------
@router.callback_query(F.data == "back_main")
async def back_main_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка кнопки 'Назад' в главное меню"""
    await state.clear()

    await callback.message.edit_text(
        get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "term_search")
async def term_search_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка кнопки 'Термин' - запрашиваем ввод термина"""
    # Проверяем регистрацию пользователя
    user = await db.get_user_profile(callback.from_user.id)

    if not user or not user.is_registered:
        await callback.message.edit_text(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )
        await callback.answer("Требуется регистрация")
        return

    await callback.message.edit_text(
        get_search_prompt(),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )

    await state.set_state(SearchStates.waiting_for_term)
    await callback.answer("Введите термин для поиска")


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка кнопки 'Главная'"""
    await state.clear()
    await callback.message.edit_text(
        get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    """Обработка перехода в 'О боте'"""
    await callback.message.edit_text(
        get_about_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery) -> None:
    """Обработка перехода в настройки"""
    await callback.message.edit_text(
        get_settings_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=settings_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def contacts_handler(callback: CallbackQuery) -> None:
    """Обработка перехода в контакты"""
    await callback.message.edit_text(
        get_contacts_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "faq")
async def faq_handler(callback: CallbackQuery) -> None:
    """Обработка перехода в FAQ"""
    await callback.message.edit_text(
        get_faq_message(),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ---------- Обработчик кнопки "Профиль" ----------
@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery) -> None:
    """Обработка кнопки 'Профиль' в главном меню"""
    # Проверяем регистрацию пользователя
    user = await db.get_user_profile(callback.from_user.id)

    if not user or not user.is_registered:
        await callback.message.edit_text(
            "⚠️ <b>Сначала нужно завершить регистрацию!</b>\n\n"
            "Используйте команду /start для регистрации.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard()
        )
        await callback.answer("Требуется регистрация")
        return

    # Показываем профиль пользователя
    profile_text = format_user_profile(user)

    await callback.message.edit_text(
        profile_text,
        parse_mode=ParseMode.HTML,
        reply_markup=profile_keyboard()  # Клавиатура профиля
    )
    await callback.answer()


# ---------- Настройки ----------
@router.callback_query(F.data.in_(["notifications", "language", "theme"]))
async def settings_options_handler(callback: CallbackQuery) -> None:
    """Обработка опций настроек"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Назад к настройкам", callback_data="settings")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
    ])

    await callback.message.edit_text(
        get_settings_option_message(callback.data),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback.answer()


# ---------- Отмена поиска ----------
@router.message(F.text.lower().in_(["отмена", "cancel", "стоп"]))
async def cancel_search_handler(message: Message, state: FSMContext) -> None:
    """Обработка команды отмены поиска"""
    current_state = await state.get_state()

    if current_state == SearchStates.waiting_for_term:
        await state.clear()
        await message.answer(
            get_cancel_search_message(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )

