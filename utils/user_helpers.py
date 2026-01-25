"""
Утилиты для работы с пользователями
"""
from datetime import datetime
from typing import Optional
from database import User

def parse_datetime(date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Парсинг строки даты"""
    try:
        return datetime.strptime(date_string, format_str)
    except (ValueError, TypeError):
        return None

def format_user_profile(user: User) -> str:
    """Форматирование профиля пользователя для отображения"""
    from .html_formatter import bold, code

    lines = []
    lines.append(f"{bold('👤 Ваш профиль')}")
    lines.append("")

    if user.first_name:
        lines.append(f"{bold('Имя:')} {user.first_name}")
    if user.last_name:
        lines.append(f"{bold('Фамилия:')} {user.last_name}")
    if user.username:
        lines.append(f"{bold('Username:')} @{user.username}")
    if user.email:
        lines.append(f"{bold('Email:')} {user.email}")
    if user.age:
        lines.append(f"{bold('Возраст:')} {user.age}")

    lines.append("")
    lines.append(f"{bold('📊 Статистика:')}")
    lines.append(f"• Поисков выполнено: {user.search_count}")

    if user.registration_date:
        reg_date = user.registration_date.strftime("%d.%m.%Y %H:%M")
        lines.append(f"• Дата регистрации: {reg_date}")

    if user.last_activity:
        last_act = user.last_activity.strftime("%d.%m.%Y %H:%M")
        lines.append(f"• Последняя активность: {last_act}")

    lines.append("")
    lines.append(f"{bold('ID:')} {code(str(user.telegram_id))}")

    return "\n".join(lines)

def validate_email(email: str) -> bool:
    """Простая валидация email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_age(age: str) -> Optional[int]:
    """Валидация возраста"""
    try:
        age_int = int(age)
        if 1 <= age_int <= 120:
            return age_int
        return None
    except ValueError:
        return None

def format_search_history_item(item) -> str:
    """Форматирование элемента истории поиска"""
    from .html_formatter import bold, code, link

    timestamp = item.timestamp.strftime("%d.%m.%Y %H:%M") if item.timestamp else "Неизвестно"

    result = []
    result.append(f"📅 {timestamp}")
    result.append(f"🔍 {bold('Запрос:')} {code(item.search_term)}")

    if item.result_title:
        result.append(f"📚 {bold('Результат:')} {item.result_title}")

    if item.result_url and item.success:
        result.append(f"🔗 {link('Открыть статью', item.result_url)}")

    if not item.success:
        result.append("❌ Поиск не удался")

    return "\n".join(result)

def format_bot_stats(stats) -> str:
    """Форматирование статистики бота"""
    from .html_formatter import bold, code, italic

    result = []
    result.append(f"{bold('📊 Статистика бота')}")
    result.append("")

    result.append(f"{bold('👥 Пользователи:')}")
    result.append(f"• Всего: {stats.total_users}")
    result.append(f"• Активных (30 дней): {stats.active_users}")
    result.append("")

    result.append(f"{bold('🔍 Поиски:')}")
    result.append(f"• Всего: {stats.total_searches}")
    result.append(f"• Успешных: {stats.successful_searches}")
    success_rate = (stats.successful_searches / stats.total_searches * 100) if stats.total_searches > 0 else 0
    result.append(f"• Успешность: {success_rate:.1f}%")
    result.append("")

    if stats.popular_terms:
        result.append(f"{bold('🏆 Популярные запросы:')}")
        for i, (term, count) in enumerate(stats.popular_terms[:5], 1):
            result.append(f"{i}. {code(term)} — {count}")

    return "\n".join(result)

def format_users_list_for_admin(users: list) -> str:
    """Форматирование списка пользователей для администратора"""
    from .html_formatter import bold, code

    if not users:
        return "📭 <b>Нет зарегистрированных пользователей.</b>"

    result = [f"{bold('👥 Список пользователей:')}\n"]

    for i, user in enumerate(users, 1):
        status = "✅" if user.is_registered else "⏳"
        reg_date = user.registration_date.strftime('%d.%m.%Y') if user.registration_date else 'Нет'

        user_info = (
            f"{i}. {status} {code(str(user.telegram_id))}\n"
            f"   👤 {user.first_name or 'Не указано'} {user.last_name or ''}\n"
            f"   📊 Поисков: {user.search_count}\n"
            f"   📅 Рег.: {reg_date}"
        )

        result.append(user_info)

    result.append(f"\n{bold('Всего пользователей:')} {len(users)}")

    return "\n\n".join(result)


def format_datetime(dt_value, date_format="%d.%m.%Y %H:%M:%S"):
    """
    Форматирование даты-времени с удалением микросекунд

    Args:
        dt_value: Значение даты (datetime объект или строка)
        date_format: Формат вывода

    Returns:
        Отформатированная строка
    """
    from datetime import datetime

    if not dt_value:
        return "Неизвестно"

    try:
        # Если это datetime объект
        if hasattr(dt_value, 'strftime'):
            # Убираем микросекунды
            if hasattr(dt_value, 'microsecond') and dt_value.microsecond:
                dt_value = dt_value.replace(microsecond=0)
            return dt_value.strftime(date_format)

        # Если это строка
        elif isinstance(dt_value, str):
            # Пытаемся распарсить строку
            # Сначала пробуем стандартный формат SQLite с микросекундами
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",  # SQLite с микросекундами
                "%Y-%m-%d %H:%M:%S",  # SQLite без микросекунд
                "%d.%m.%Y %H:%M:%S",  # Наш формат
                "%d.%m.%Y %H:%M"  # Без секунд
            ]:
                try:
                    dt_obj = datetime.strptime(dt_value, fmt)
                    # Убираем микросекунды
                    dt_obj = dt_obj.replace(microsecond=0)
                    return dt_obj.strftime(date_format)
                except ValueError:
                    continue

            # Если не удалось распарсить, убираем микросекунды из строки
            if '.' in dt_value:
                parts = dt_value.split('.')
                # Берем только часть до точки (целые секунды)
                return parts[0]

            return dt_value

    except Exception:
        # В случае ошибки возвращаем исходное значение
        return str(dt_value)
