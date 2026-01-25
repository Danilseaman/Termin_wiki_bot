import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация бота"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(','))) if os.getenv("ADMIN_IDS") else []

    # Настройки базы данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")

    # Настройки
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @property
    def is_sqlite(self):
        return self.DATABASE_URL.startswith("sqlite")


config = Config()

