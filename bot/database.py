import sqlite3
import os
from datetime import datetime

DB_PATH = "bot_data.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        language TEXT DEFAULT 'ru',
        is_banned INTEGER DEFAULT 0,
        captcha_passed INTEGER DEFAULT 0,
        total_orders INTEGER DEFAULT 0,
        registered_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bot_type TEXT,
        description TEXT,
        price_uah REAL,
        currency TEXT DEFAULT 'UAH',
        unique_kopecks TEXT,
        unique_kopecks2 TEXT,
        status TEXT DEFAULT 'new',
        prepay_confirmed INTEGER DEFAULT 0,
        finalpay_confirmed INTEGER DEFAULT 0,
        delivery_link TEXT,
        casino_discount INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS payment_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        user_id INTEGER,
        pay_type TEXT,
        amount REAL,
        currency TEXT,
        pressed_at TEXT,
        confirmed_at TEXT,
        status TEXT DEFAULT 'pending'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS casino_plays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bet INTEGER,
        result TEXT,
        prize TEXT,
        played_at TEXT
    )""")

    conn.commit()
    conn.close()

# --- USER ---
def get_user(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row

def create_user(user_id, username, full_name):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, full_name, registered_at) VALUES (?,?,?,?)",
        (user_id, username, full_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def set_captcha_passed(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET captcha_passed=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def set_user_lang(user_id, lang):
    conn = get_conn()
    conn.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT user_id, full_name, username, total_orders FROM users ORDER BY total_orders DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows

# --- ORDERS ---
def create_order(user_id, bot_type, description, price_uah, currency, unique_kopecks, unique_kopecks2):
    conn = get_conn()
    now = datetime.now().isoformat()
    c = conn.execute(
        """INSERT INTO orders (user_id,bot_type,description,price_uah,currency,unique_kopecks,unique_kopecks2,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (user_id, bot_type, description, price_uah, currency, unique_kopecks, unique_kopecks2, now, now)
    )
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    return row

def get_user_orders(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows

def update_order_status(order_id, status):
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET status=?, updated_at=? WHERE id=?",
        (status, datetime.now().isoformat(), order_id)
    )
    conn.commit()
    conn.close()

def confirm_prepay(order_id):
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET prepay_confirmed=1, status='in_work', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), order_id)
    )
    conn.commit()
    conn.close()

def confirm_finalpay(order_id):
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET finalpay_confirmed=1, status='completed', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), order_id)
    )
    # +1 к заказам пользователя
    row = conn.execute("SELECT user_id FROM orders WHERE id=?", (order_id,)).fetchone()
    if row:
        conn.execute("UPDATE users SET total_orders=total_orders+1 WHERE user_id=?", (row["user_id"],))
    conn.commit()
    conn.close()

def set_delivery_link(order_id, link):
    conn = get_conn()
    conn.execute("UPDATE orders SET delivery_link=? WHERE id=?", (link, order_id))
    conn.commit()
    conn.close()

def cancel_order(order_id):
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET status='cancelled', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), order_id)
    )
    conn.commit()
    conn.close()

# --- PAYMENT LOGS ---
def log_payment(order_id, user_id, pay_type, amount, currency):
    conn = get_conn()
    conn.execute(
        "INSERT INTO payment_logs (order_id,user_id,pay_type,amount,currency,pressed_at,status) VALUES (?,?,?,?,?,?,?)",
        (order_id, user_id, pay_type, amount, currency, datetime.now().isoformat(), "pending")
    )
    conn.commit()
    conn.close()

# --- CASINO ---
def log_casino(user_id, bet, result, prize):
    conn = get_conn()
    conn.execute(
        "INSERT INTO casino_plays (user_id,bet,result,prize,played_at) VALUES (?,?,?,?,?)",
        (user_id, bet, result, prize, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
