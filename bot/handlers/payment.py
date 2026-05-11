from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS
from keyboards import admin_payment_kb, final_pay_kb, back_kb, deliver_kb
from translations import t
from utils import now_str, now_display, get_payment_details
import logging

router = Router()
logger = logging.getLogger(__name__)

class DeliveryState(StatesGroup):
    waiting_link = State()

# =====================
# ЮЗЕР: нажал "Я оплатил" (предоплата)
# =====================
@router.callback_query(F.data.startswith("paid_") & F.data.endswith("_prepay"))
async def user_paid_prepay(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id = int(parts[1])

    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    order = db.get_order(order_id)

    if not order:
        await call.answer("Заказ не найден")
        return

    press_time = now_str()
    db.log_payment(order_id, call.from_user.id, "prepay", float(order["unique_kopecks"]), order["currency"])

    # Уведомляем всех админов
    admin_text = (
        f"💰 <b>НОВЫЙ ПЛАТЁЖ — Предоплата 50%</b>\n\n"
        f"📦 Заказ #{order_id}\n"
        f"👤 Пользователь: {call.from_user.full_name} (@{call.from_user.username or 'нет'})\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"🤖 Тип бота: {order['bot_type']}\n"
        f"💵 Сумма: <b>{order['unique_kopecks']} {order['currency']}</b>\n"
        f"⏰ Нажал в: <b>{press_time}</b>\n\n"
        f"📝 ТЗ:\n{order['description'][:500]}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_payment_kb(order_id, "prepay"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

    await call.message.edit_text(
        t("wait_confirm", lang),
        reply_markup=back_kb(),
        parse_mode="HTML"
    )

# =====================
# ЮЗЕР: нажал "Я оплатил" (финальная)
# =====================
@router.callback_query(F.data.startswith("paid_") & F.data.endswith("_final"))
async def user_paid_final(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id = int(parts[1])

    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    order = db.get_order(order_id)

    if not order:
        await call.answer("Заказ не найден")
        return

    press_time = now_str()
    db.log_payment(order_id, call.from_user.id, "final", float(order["unique_kopecks2"]), order["currency"])

    admin_text = (
        f"💰 <b>НОВЫЙ ПЛАТЁЖ — Финальная оплата 50%</b>\n\n"
        f"📦 Заказ #{order_id}\n"
        f"👤 Пользователь: {call.from_user.full_name} (@{call.from_user.username or 'нет'})\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"🤖 Тип бота: {order['bot_type']}\n"
        f"💵 Сумма: <b>{order['unique_kopecks2']} {order['currency']}</b>\n"
        f"⏰ Нажал в: <b>{press_time}</b>"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_payment_kb(order_id, "final"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

    await call.message.edit_text(
        t("wait_confirm", lang),
        reply_markup=back_kb(),
        parse_mode="HTML"
    )

# =====================
# ФИНАЛЬНАЯ ОПЛАТА — кнопка из корзины/уведомления
# =====================
@router.callback_query(F.data.startswith("finalpay_"))
async def show_finalpay(call: CallbackQuery):
    order_id = int(call.data.split("_")[1])
    order = db.get_order(order_id)
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    if not order:
        await call.answer("Заказ не найден")
        return

    details = get_payment_details(order["currency"])
    text = t("pay_prepay", lang,
             amount=order["unique_kopecks2"],
             currency=order["currency"],
             details=details).replace("Предоплата 50%", "Финальная оплата 50%").replace("Prepayment", "Final payment")

    await call.message.edit_text(
        text,
        reply_markup=final_pay_kb(order_id, lang),
        parse_mode="HTML"
    )

# =====================
# ADMIN: Подтвердить предоплату
# =====================
@router.callback_query(F.data.startswith("admin_confirm_") & F.data.endswith("_prepay"))
async def admin_confirm_prepay(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id = int(parts[2])
    confirm_time = now_display()

    db.confirm_prepay(order_id)
    order = db.get_order(order_id)

    if not order:
        await call.answer("Заказ не найден")
        return

    row = db.get_user(order["user_id"])
    lang = row["language"] if row else "ru"

    # Сообщаем юзеру
    try:
        await bot.send_message(
            order["user_id"],
            t("prepay_confirmed", lang, time=confirm_time, order_id=order_id),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки юзеру {order['user_id']}: {e}")

    await call.message.edit_text(
        f"✅ Предоплата по заказу #{order_id} подтверждена в {confirm_time}",
        parse_mode="HTML"
    )

# =====================
# ADMIN: Подтвердить финальную оплату → выдать ссылку
# =====================
@router.callback_query(F.data.startswith("admin_confirm_") & F.data.endswith("_final"))
async def admin_confirm_final(call: CallbackQuery, bot: Bot, state: FSMContext):
    parts = call.data.split("_")
    order_id = int(parts[2])

    await state.set_state(DeliveryState.waiting_link)
    await state.update_data(order_id=order_id, admin_msg_id=call.message.message_id)

    await call.message.edit_text(
        f"📦 Финальная оплата по заказу #{order_id} подтверждена!\n\n"
        f"Теперь отправьте ссылку на архив/код для клиента:"
    )

@router.message(DeliveryState.waiting_link)
async def got_delivery_link(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    link = message.text
    await state.clear()

    db.confirm_finalpay(order_id)
    db.set_delivery_link(order_id, link)

    order = db.get_order(order_id)
    row = db.get_user(order["user_id"])
    lang = row["language"] if row else "ru"
    confirm_time = now_display()

    try:
        await bot.send_message(
            order["user_id"],
            t("delivery", lang, time=confirm_time, link=link),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(e)

    await message.answer(f"✅ Ссылка отправлена клиенту. Заказ #{order_id} завершён!")

# =====================
# ADMIN: Отменить
# =====================
@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id = int(parts[2])
    db.cancel_order(order_id)
    order = db.get_order(order_id)

    if order:
        row = db.get_user(order["user_id"])
        lang = row["language"] if row else "ru"
        try:
            await bot.send_message(
                order["user_id"],
                f"❌ Ваш платёж по заказу #{order_id} не подтверждён.\n"
                f"Пожалуйста, свяжитесь с поддержкой.",
            )
        except Exception:
            pass

    await call.message.edit_text(f"❌ Заказ #{order_id} отменён.")

# =====================
# ADMIN: Бан
# =====================
@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id = int(parts[2])
    order = db.get_order(order_id)
    if order:
        db.ban_user(order["user_id"])
        await call.answer(f"🚫 Пользователь {order['user_id']} заблокирован!")
        await call.message.edit_text(f"🚫 Пользователь {order['user_id']} заблокирован.")
    else:
        await call.answer("Заказ не найден")
