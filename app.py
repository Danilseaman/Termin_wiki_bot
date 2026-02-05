import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import os
import sys
from config import config
from handlers import routers
from database import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных инициализирована")

    # Получаем статистику для логов
    stats = await db.get_bot_stats()
    logger.info(f"Загружено пользователей: {stats.total_users}")
    logger.info(f"Всего поисков: {stats.total_searches}")


async def on_shutdown(bot: Bot):
    """Действия при выключении бота"""
    logger.info("Бот выключается...")
    # Закрываем соединения
    logger.info("Соединения закрыты")


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

    try:
        # Запускаем long polling (лучше для Railway)
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Проверяем, что BOT_TOKEN установлен
    if not config.BOT_TOKEN and not os.environ.get("BOT_TOKEN"):
        logger.error("BOT_TOKEN не найден ни в config.py, ни в переменных окружения!")
        sys.exit(1)

    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")