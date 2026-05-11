import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, catalog, cart, casino, support, payment, admin

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def init_db():
    """Создает все необходимые таблицы, чтобы не было ошибок 'no such table'"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    
    # Таблица категорий (для каталога)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    
    # Таблица товаров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            description TEXT,
            price REAL,
            photo_id TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)
    
    # Таблица корзины
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных проверена и готова!")

async def main():
    # Запускаем создание базы
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутеры
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(casino.router)
    dp.include_router(support.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    # Чистим очередь обновлений, чтобы не было ошибок Conflict
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🚀 Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
