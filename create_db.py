#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""
import asyncio
from database import db


async def main():
    print("Инициализация базы данных...")
    await db.init_db()
    print("База данных успешно создана!")

    # Проверяем соединение
    stats = await db.get_bot_stats()
    print(f"Пользователей в базе: {stats.total_users}")
    print(f"Поисков в базе: {stats.total_searches}")


if __name__ == "__main__":
    asyncio.run(main())