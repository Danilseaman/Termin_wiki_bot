from aiogram import Router
from aiogram.types import ErrorEvent
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.error()
async def error_handler(event: ErrorEvent):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {event.exception}", exc_info=True)

    # Можно отправить сообщение администратору
    # или пользователю в зависимости от ошибки

    return True  # Предотвращает дальнейшую обработку ошибки