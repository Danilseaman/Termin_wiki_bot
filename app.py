import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
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

    # Установка вебхука
    webhook_url = get_webhook_url()
    await bot.set_webhook(webhook_url)
    logger.info(f"Вебхук установлен на {webhook_url}")


async def on_shutdown(bot: Bot):
    """Действия при выключении бота"""
    logger.info("Бот выключается...")
    # Удаляем вебхук при выключении
    await bot.delete_webhook()
    logger.info("Вебхук удален")


def get_webhook_url():
    """Получение URL для вебхука"""
    # Получаем базовый URL из переменных окружения
    base_url = os.environ.get("RAILWAY_STATIC_URL")

    if not base_url:
        # Если Railway не предоставил URL, используем альтернативные варианты
        railway_public_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        if railway_public_url:
            base_url = f"https://{railway_public_url}"
        else:
            # Для локальной разработки или если переменные не установлены
            base_url = "https://your-app-name.up.railway.app"

    # Убираем возможный слеш в конце
    base_url = base_url.rstrip('/')
    webhook_path = "/webhook"

    return f"{base_url}{webhook_path}"


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

    # Создаем aiohttp приложение
    app = web.Application()

    # Создаем обработчик вебхуков для aiogram
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.environ.get("WEBHOOK_SECRET")  # Опционально для безопасности
    )

    # Регистрируем путь для вебхука
    webhook_handler.register(app, path="/webhook")

    # Опционально: добавляем health check endpoint
    async def health_check(request):
        return web.Response(text="Bot is running")

    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    # Получаем порт из переменных окружения (Railway предоставляет PORT)
    port = int(os.environ.get("PORT", 8443))

    # Настраиваем запуск сервера
    runner = web.AppRunner(app)
    await runner.setup()

    # Запускаем на всех интерфейсах и указанном порте
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Сервер запущен на порту {port}")
    logger.info(f"Вебхук будет доступен по адресу: {get_webhook_url()}")

    # Бесконечный цикл ожидания
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал на остановку...")
    finally:
        logger.info("Остановка сервера...")
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    # Проверяем, что BOT_TOKEN установлен
    if not config.BOT_TOKEN and not os.environ.get("BOT_TOKEN"):
        logger.error("BOT_TOKEN не найден ни в config.py, ни в переменных окружения!")
        sys.exit(1)

    # Проверяем переменные окружения для Railway
    if not os.environ.get("PORT"):
        logger.warning("Переменная окружения PORT не установлена. Использую порт 8443")

    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")