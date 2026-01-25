"""
Репозиторий для работы с базой данных
"""
import aiosqlite
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Any
from dataclasses import asdict
import json
from .models import User, SearchHistory, BotStats


class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_db_lock = asyncio.Lock()

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Включаем поддержку внешних ключей
            await db.execute("PRAGMA foreign_keys = ON")

            # Создаем таблицу пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    age INTEGER,
                    is_registered BOOLEAN DEFAULT FALSE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    search_count INTEGER DEFAULT 0
                )
            ''')

            # Создаем таблицу истории поиска
            await db.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    search_term TEXT NOT NULL,
                    result_title TEXT,
                    result_url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')

            # Индексы для ускорения запросов
            await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(telegram_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_search_user_id ON search_history(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_history(timestamp)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_search_term ON search_history(search_term)')

            await db.commit()

    async def _parse_user_row(self, row: Tuple[Any, ...]) -> Optional[User]:
        """Парсинг строки пользователя из базы данных"""
        if not row:
            return None

        try:
            return User(
                id=row[0],
                telegram_id=row[1],
                username=row[2],
                first_name=row[3],
                last_name=row[4],
                email=row[5],
                age=row[6],
                is_registered=bool(row[7]),
                registration_date=row[8],  # Оставляем как есть, парсим в модели
                last_activity=row[9],  # Оставляем как есть, парсим в моделях
                search_count=row[10]
            )
        except Exception as e:
            print(f"Ошибка парсинга пользователя: {e}")
            return None

    async def _parse_search_history_row(self, row: Tuple[Any, ...]) -> Optional[SearchHistory]:
        """Парсинг строки истории поиска из базы данных"""
        if not row:
            return None

        try:
            return SearchHistory(
                id=row[0],
                user_id=row[1],
                search_term=row[2],
                result_title=row[3],
                result_url=row[4],
                timestamp=row[5],  # Оставляем как есть, парсим в моделях
                success=bool(row[6])
            )
        except Exception as e:
            print(f"Ошибка парсинга истории поиска: {e}")
            return None

    async def get_or_create_user(self, telegram_id: int, username: str = None,
                                 first_name: str = None, last_name: str = None) -> User:
        """Получить или создать пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Ищем пользователя
            cursor = await db.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if row:
                # Пользователь найден, обновляем последнюю активность
                user = await self._parse_user_row(row)
                if not user:
                    # Если не удалось распарсить, создаем нового
                    user_id = 0
                else:
                    user_id = user.id

                await db.execute(
                    'UPDATE users SET last_activity = ?, username = ? WHERE id = ?',
                    (datetime.now().isoformat(), username or (user.username if user else None), user_id)
                )
                await db.commit()

                if user:
                    return user
                else:
                    # Если пользователь не распарсился, получаем заново
                    cursor = await db.execute(
                        'SELECT * FROM users WHERE telegram_id = ?',
                        (telegram_id,)
                    )
                    row = await cursor.fetchone()
                    return await self._parse_user_row(row) or User(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        registration_date=datetime.now().isoformat(),
                        last_activity=datetime.now().isoformat()
                    )
            else:
                # Создаем нового пользователя
                current_time = datetime.now().isoformat()
                cursor = await db.execute('''
                    INSERT INTO users 
                    (telegram_id, username, first_name, last_name, registration_date, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                    current_time,
                    current_time
                ))

                await db.commit()
                user_id = cursor.lastrowid

                # Получаем созданного пользователя
                cursor = await db.execute(
                    'SELECT * FROM users WHERE id = ?',
                    (user_id,)
                )
                row = await cursor.fetchone()
                return await self._parse_user_row(row) or User(
                    id=user_id,
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    registration_date=current_time,
                    last_activity=current_time
                )

    async def update_user_profile(self, telegram_id: int, email: str = None,
                                  age: int = None, first_name: str = None,
                                  last_name: str = None) -> bool:
        """Обновить профиль пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала получаем текущие данные
            cursor = await db.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return False

            user = await self._parse_user_row(row)

            if not user:
                return False

            # Обновляем только переданные поля
            update_fields = []
            params = []

            if email is not None:
                update_fields.append("email = ?")
                params.append(email)

            if age is not None:
                update_fields.append("age = ?")
                params.append(age)

            if first_name is not None:
                update_fields.append("first_name = ?")
                params.append(first_name)

            if last_name is not None:
                update_fields.append("last_name = ?")
                params.append(last_name)

            if not update_fields:
                return False

            update_fields.append("is_registered = ?")
            params.append(True)

            # Обновляем время последней активности
            update_fields.append("last_activity = ?")
            params.append(datetime.now().isoformat())

            params.append(telegram_id)

            query = f"UPDATE users SET {', '.join(update_fields)} WHERE telegram_id = ?"
            await db.execute(query, params)
            await db.commit()

            return True

    async def add_search_history(self, telegram_id: int, search_term: str,
                                 result_title: str = None, result_url: str = None,
                                 success: bool = True) -> bool:
        """Добавить запись в историю поиска"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем ID пользователя
            cursor = await db.execute(
                'SELECT id FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return False

            user_id = row[0]

            # Добавляем запись в историю
            await db.execute('''
                INSERT INTO search_history 
                (user_id, search_term, result_title, result_url, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, search_term, result_title, result_url, datetime.now().isoformat(), success))

            # Обновляем счетчик поисков пользователя
            await db.execute(
                'UPDATE users SET search_count = search_count + 1, last_activity = ? WHERE id = ?',
                (datetime.now().isoformat(), user_id)
            )

            await db.commit()
            return True

    async def get_user_search_history(self, telegram_id: int, limit: int = 10) -> List[SearchHistory]:
        """Получить историю поиска пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем ID пользователя
            cursor = await db.execute(
                'SELECT id FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return []

            user_id = row[0]

            # Получаем историю поиска
            cursor = await db.execute('''
                SELECT * FROM search_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))

            rows = await cursor.fetchall()
            history = []
            for row in rows:
                item = await self._parse_search_history_row(row)
                if item:
                    history.append(item)

            return history

    async def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Получить профиль пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if row:
                return await self._parse_user_row(row)
            return None

    async def get_bot_stats(self) -> BotStats:
        """Получить статистику бота"""
        async with aiosqlite.connect(self.db_path) as db:
            # Общее количество пользователей
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]

            # Активные пользователи (за последние 30 дней)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor = await db.execute(
                'SELECT COUNT(DISTINCT user_id) FROM search_history WHERE timestamp > ?',
                (thirty_days_ago,)
            )
            active_users = (await cursor.fetchone())[0]

            # Общее количество поисков
            cursor = await db.execute('SELECT COUNT(*) FROM search_history')
            total_searches = (await cursor.fetchone())[0]

            # Успешные поиски
            cursor = await db.execute('SELECT COUNT(*) FROM search_history WHERE success = TRUE')
            successful_searches = (await cursor.fetchone())[0]

            # Популярные термины
            cursor = await db.execute('''
                SELECT search_term, COUNT(*) as count 
                FROM search_history 
                GROUP BY search_term 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            popular_terms = [(row[0], row[1]) for row in await cursor.fetchall()]

            return BotStats(
                total_users=total_users,
                active_users=active_users,
                total_searches=total_searches,
                successful_searches=successful_searches,
                popular_terms=popular_terms
            )

    async def get_user_stats(self, telegram_id: int) -> dict:
        """Получить статистику пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем пользователя
            cursor = await db.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return {}

            user = User(*row)
            user_id = user.id

            # Статистика поисков пользователя
            cursor = await db.execute('''
                SELECT COUNT(*) as total_searches,
                       SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful_searches,
                       MIN(timestamp) as first_search,
                       MAX(timestamp) as last_search
                FROM search_history 
                WHERE user_id = ?
            ''', (user_id,))

            stats_row = await cursor.fetchone()

            # Популярные термины пользователя
            cursor = await db.execute('''
                SELECT search_term, COUNT(*) as count 
                FROM search_history 
                WHERE user_id = ?
                GROUP BY search_term 
                ORDER BY count DESC 
                LIMIT 5
            ''', (user_id,))

            user_popular_terms = [(row[0], row[1]) for row in await cursor.fetchall()]

            # Функция для форматирования даты из базы
            def format_db_datetime(db_datetime):
                """Форматирует дату из базы в формат '18.01.2026 12:13'"""
                from datetime import datetime

                if not db_datetime:
                    return None

                try:
                    # Если это уже datetime объект
                    if hasattr(db_datetime, 'strftime'):
                        # Форматируем без секунд
                        return db_datetime.strftime("%d.%m.%Y %H:%M")

                    # Если это строка
                    db_datetime_str = str(db_datetime)

                    # Убираем микросекунды если есть
                    if '.' in db_datetime_str:
                        db_datetime_str = db_datetime_str.split('.')[0]

                    # Заменяем T на пробел если есть ISO формат
                    db_datetime_str = db_datetime_str.replace('T', ' ')

                    # Пробуем разные форматы
                    formats_to_try = [
                        "%Y-%m-%d %H:%M:%S",  # SQLite стандарт
                        "%Y-%m-%d %H:%M",  # Без секунд
                        "%d.%m.%Y %H:%M:%S",  # Наш формат с секундами
                        "%d.%m.%Y %H:%M",  # Наш формат без секунд
                        "%Y-%m-%d",  # Только дата
                        "%d.%m.%Y"  # Только дата наш
                    ]

                    for fmt in formats_to_try:
                        try:
                            dt = datetime.strptime(db_datetime_str, fmt)
                            # Для первого поиска - только дата
                            if fmt.endswith("%Y"):  # Если только дата в формате
                                return dt.strftime("%d.%m.%Y")
                            else:
                                # Убираем секунды
                                return dt.strftime("%d.%m.%Y %H:%M")
                        except ValueError:
                            continue

                    # Если не удалось распарсить, возвращаем как есть
                    return db_datetime_str

                except Exception:
                    return str(db_datetime)

            # Форматируем даты
            first_search = None
            last_search = None

            if stats_row and stats_row[2]:  # first_search
                first_search = format_db_datetime(stats_row[2])
                # Для первого поиска оставляем только дату
                if first_search and ' ' in first_search:
                    first_search = first_search.split(' ')[0]

            if stats_row and stats_row[3]:  # last_search
                last_search = format_db_datetime(stats_row[3])

            return {
                'user': user,
                'total_searches': stats_row[0] if stats_row else 0,
                'successful_searches': stats_row[1] if stats_row else 0,
                'first_search': first_search,  # Уже отформатированная строка
                'last_search': last_search,  # Уже отформатированная строка
                'popular_terms': user_popular_terms
            }

    async def get_all_users(self, limit: int = 100) -> List[User]:
        """Получить всех пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM users 
                ORDER BY last_activity DESC 
                LIMIT ?
            ''', (limit,))

            rows = await cursor.fetchall()
            users = []
            for row in rows:
                user = await self._parse_user_row(row)
                if user:
                    users.append(user)

            return users

    async def delete_user_data(self, telegram_id: int) -> bool:
        """Удалить данные пользователя (GDPR compliance)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Получаем ID пользователя
                cursor = await db.execute(
                    'SELECT id FROM users WHERE telegram_id = ?',
                    (telegram_id,)
                )
                row = await cursor.fetchone()

                if not row:
                    return False

                user_id = row[0]

                # Удаляем историю поиска
                await db.execute(
                    'DELETE FROM search_history WHERE user_id = ?',
                    (user_id,)
                )

                # Удаляем пользователя
                await db.execute(
                    'DELETE FROM users WHERE id = ?',
                    (user_id,)
                )

                await db.commit()
                return True
            except Exception as e:
                print(f"Ошибка при удалении данных пользователя: {e}")
                return False

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM users WHERE id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()

            if row:
                return await self._parse_user_row(row)
            return None

    async def update_last_activity(self, telegram_id: int) -> bool:
        """Обновить время последней активности пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    'UPDATE users SET last_activity = ? WHERE telegram_id = ?',
                    (datetime.now().isoformat(), telegram_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Ошибка обновления активности пользователя: {e}")
                return False

    async def get_recent_searches(self, hours: int = 24, limit: int = 50) -> List[SearchHistory]:
        """Получить последние поиски за указанное количество часов"""
        async with aiosqlite.connect(self.db_path) as db:
            time_threshold = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor = await db.execute('''
                SELECT sh.* FROM search_history sh
                JOIN users u ON sh.user_id = u.id
                WHERE sh.timestamp > ?
                ORDER BY sh.timestamp DESC
                LIMIT ?
            ''', (time_threshold, limit))

            rows = await cursor.fetchall()
            searches = []
            for row in rows:
                item = await self._parse_search_history_row(row)
                if item:
                    searches.append(item)

            return searches

    async def cleanup_old_data(self, days: int = 365) -> int:
        """Очистка старых данных (истории поиска старше указанного количества дней)"""
        async with aiosqlite.connect(self.db_path) as db:
            time_threshold = (datetime.now() - timedelta(days=days)).isoformat()

            cursor = await db.execute(
                'DELETE FROM search_history WHERE timestamp < ?',
                (time_threshold,)
            )

            deleted_count = cursor.rowcount
            await db.commit()

            return deleted_count


# Создаем глобальный экземпляр базы данных
db = Database()