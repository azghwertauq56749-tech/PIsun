import asyncio
import logging
import sqlite3
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем твои модули (те, что у тебя есть)
from config import BOT_TOKEN
from handlers import start, catalog, cart, casino, support, payment, admin

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ ---
def fix_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Создаем таблицу пользователей принудительно
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Таблица users проверена!")

async def main():
    # Запускаем исправление перед включением бота
    fix_database()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем твои разделы
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(casino.router)
    dp.include_router(support.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    # Удаляем старые сообщения (чтобы не было ошибки Conflict)
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🚀 Бот запущен!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
