from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS
from keyboards import deliver_kb

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

class NotifyState(StatesGroup):
    waiting_order_id = State()
    waiting_link = State()

# /admin — панель
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="adm_orders")],
        [InlineKeyboardButton(text="🎊 Уведомить о готовности", callback_data="adm_notify")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
    ])
    await message.answer("⚙️ <b>Панель администратора</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "adm_orders")
async def adm_orders(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status NOT IN ('completed','cancelled') ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()

    if not rows:
        await call.answer("Нет активных заказов")
        return

    text = "📋 <b>Активные заказы:</b>\n\n"
    for r in rows:
        text += f"#{r['id']} | {r['bot_type'][:20]} | {r['status']} | {r['currency']} | user:{r['user_id']}\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await call.message.edit_text(text[:4000], parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back")]
        ])
    )

@router.callback_query(F.data == "adm_notify")
async def adm_notify(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(NotifyState.waiting_order_id)
    await call.message.edit_text("Введите номер заказа (#ID), который готов:")

@router.message(NotifyState.waiting_order_id)
async def got_order_id(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = int(message.text.replace("#", "").strip())
    except ValueError:
        await message.answer("Неверный ID. Введите число.")
        return

    order = db.get_order(order_id)
    if not order:
        await message.answer(f"Заказ #{order_id} не найден.")
        await state.clear()
        return

    db.update_order_status(order_id, "ready_for_finalpay")

    row = db.get_user(order["user_id"])
    lang = row["language"] if row else "ru"

    from translations import t
    from keyboards import final_pay_kb
    try:
        await bot.send_message(
            order["user_id"],
            t("bot_ready", lang, order_id=order_id, bot_type=order["bot_type"]),
            reply_markup=final_pay_kb(order_id, lang),
            parse_mode="HTML"
        )
        await message.answer(f"✅ Клиент по заказу #{order_id} уведомлён о готовности!")
    except Exception as e:
        await message.answer(f"Ошибка отправки: {e}")

    await state.clear()

@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    conn = db.get_conn()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM orders WHERE status='completed'").fetchone()[0]
    in_work = conn.execute("SELECT COUNT(*) FROM orders WHERE status='in_work'").fetchone()[0]
    conn.close()

    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"📦 Всего заказов: {total_orders}\n"
        f"⚙️ В работе: {in_work}\n"
        f"✅ Завершено: {completed}\n"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await call.message.edit_text(text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back")]
        ])
    )

@router.callback_query(F.data == "adm_back")
async def adm_back(call: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="adm_orders")],
        [InlineKeyboardButton(text="🎊 Уведомить о готовности", callback_data="adm_notify")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
    ])
    await call.message.edit_text("⚙️ <b>Панель администратора</b>", reply_markup=kb, parse_mode="HTML")
