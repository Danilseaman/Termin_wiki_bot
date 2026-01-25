import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import routers
from database import db
import os
import sys
from threading import Thread

# Проверяем, запущены ли на Render
def is_render():
    return "RENDER" in os.environ

# Функция для поддержания работы на Render
def keep_alive( ):
    if is_render():
        from flask import Flask
        app = Flask("")

        @app.route('/')
        def home():
            return "Бот запущен!"

        def run():
            app.run(host="0.0.0.0", port=8080)

        t = Thread(target=run)
        t.start()


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных инициализирована")

    # Получаем статистику для логов
    stats = await db.get_bot_stats()
    logger.info(f"Загружено пользователей: {stats.total_users}")
    logger.info(f"Всего поисков: {stats.total_searches}")


async def on_shutdown():
    """Действия при выключении бота"""
    logger.info("Бот выключается...")


async def main():
    """Основная функция запуска бота"""

    # Проверка токена
    if not config.BOT_TOKEN:
        logger.error("Не указан BOT_TOKEN в конфигурации!")
        return

    # Инициализация бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Инициализация диспетчера
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем обработчики запуска и выключения
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Подключение роутеров
    for router in routers:
        dp.include_router(router)

    # Запуск поллинга
    logger.info("Бот запущен на Render...")

    try:
        # Удаляем вебхук если был установлен
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Запускаем keep-alive сервер для Render
    if is_render():
        keep_alive()

    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")