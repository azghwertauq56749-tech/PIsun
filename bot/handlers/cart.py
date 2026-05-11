from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from translations import t
from keyboards import cart_kb, order_detail_kb, back_kb

router = Router()

STATUS_TEXT = {
    "new":                  "🆕 Новый — ожидает оплаты",
    "in_work":              "⚙️ В работе",
    "ready_for_finalpay":   "🎊 Готов — ожидает финальной оплаты",
    "completed":            "✅ Завершён",
    "cancelled":            "❌ Отменён",
}

@router.callback_query(F.data == "cart")
async def show_cart(call: CallbackQuery):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    orders = db.get_user_orders(call.from_user.id)

    if not orders:
        await call.message.edit_text(
            t("cart_empty", lang),
            reply_markup=back_kb()
        )
        return

    text = "🛒 <b>Ваши заказы / Your orders</b>\n\n"
    for o in orders[:10]:
        status = STATUS_TEXT.get(o["status"], o["status"])
        text += f"#{o['id']} — {o['bot_type'][:25]}\n{status}\n\n"

    await call.message.edit_text(
        text,
        reply_markup=cart_kb(orders, lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("order_detail_"))
async def order_detail(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    order = db.get_order(order_id)
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    if not order or order["user_id"] != call.from_user.id:
        await call.answer("Заказ не найден")
        return

    status = STATUS_TEXT.get(order["status"], order["status"])
    prepay = "✅" if order["prepay_confirmed"] else "❌"
    finalpay = "✅" if order["finalpay_confirmed"] else "❌"

    text = (
        f"📦 <b>Заказ #{order['id']}</b>\n\n"
        f"🤖 {order['bot_type']}\n"
        f"📝 {order['description'][:200]}\n\n"
        f"💵 Сумма: {order['unique_kopecks']} {order['currency']} (предоплата)\n"
        f"💵 Итого: {order['unique_kopecks2']} {order['currency']} (финал)\n\n"
        f"Предоплата: {prepay}\n"
        f"Финальная: {finalpay}\n"
        f"Статус: {status}\n"
        f"Создан: {order['created_at'][:16]}\n"
    )

    if order["delivery_link"]:
        text += f"\n📎 Ссылка: {order['delivery_link']}"

    await call.message.edit_text(
        text,
        reply_markup=order_detail_kb(order_id, order["status"], lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    order = db.get_order(order_id)
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    if not order or order["user_id"] != call.from_user.id:
        await call.answer("Нет доступа")
        return

    if order["status"] in ("completed",):
        await call.answer("Нельзя отменить завершённый заказ")
        return

    db.cancel_order(order_id)
    await call.answer("❌ Заказ отменён")
    await call.message.edit_text(
        f"❌ Заказ #{order_id} отменён.",
        reply_markup=back_kb("cart")
    )
