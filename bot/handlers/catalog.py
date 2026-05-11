from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from translations import t
from keyboards import catalog_kb, currency_kb, pay_kb, back_kb
from data.catalog import get_bot_by_id, get_bot_name
from utils import generate_unique_amount, convert_price, get_payment_details, now_str

router = Router()

class OrderFlow(StatesGroup):
    waiting_tz = State()
    waiting_currency = State()

@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    await call.message.edit_text(
        t("catalog", lang),
        reply_markup=catalog_kb(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("bot_"))
async def bot_selected(call: CallbackQuery, state: FSMContext):
    bot_id = call.data[4:]
    bot = get_bot_by_id(bot_id)
    if not bot:
        await call.answer("Бот не найден")
        return

    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    name = get_bot_name(bot, lang)
    desc = bot.get("desc_ru", "")

    text = (
        f"{bot['emoji']} <b>{name}</b>\n\n"
        f"📝 {desc}\n\n"
        f"💰 Базовая цена от <b>{bot['price_uah']} UAH</b>\n\n"
        + t("enter_tz", lang, bot_type=name)
    )

    await state.set_state(OrderFlow.waiting_tz)
    await state.update_data(bot_id=bot_id)
    await call.message.edit_text(text, reply_markup=back_kb("catalog"), parse_mode="HTML")

@router.message(OrderFlow.waiting_tz)
async def got_tz(message: Message, state: FSMContext):
    row = db.get_user(message.from_user.id)
    lang = row["language"] if row else "ru"

    if len(message.text) < 10:
        await message.answer(
            "⚠️ ТЗ слишком короткое. Напишите подробнее (минимум 10 символов)."
        )
        return

    await state.update_data(tz=message.text)
    await state.set_state(OrderFlow.waiting_currency)
    await message.answer(
        t("choose_currency", lang),
        reply_markup=currency_kb(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("curr_"), OrderFlow.waiting_currency)
async def currency_selected(call: CallbackQuery, state: FSMContext):
    currency = call.data[5:]  # UAH / USD / EUR
    data = await state.get_data()
    bot_id = data.get("bot_id")
    tz = data.get("tz", "")
    await state.clear()

    bot = get_bot_by_id(bot_id)
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    if not bot:
        await call.answer("Ошибка")
        return

    base_price = convert_price(bot["price_uah"], currency)
    half = round(base_price / 2, 2)

    # Генерируем уникальные копейки для обоих платежей
    amount1_str = generate_unique_amount(half, currency)
    amount2_str = generate_unique_amount(half, currency)

    order_id = db.create_order(
        user_id=call.from_user.id,
        bot_type=get_bot_name(bot, lang),
        description=tz,
        price_uah=bot["price_uah"],
        currency=currency,
        unique_kopecks=amount1_str,
        unique_kopecks2=amount2_str,
    )

    details = get_payment_details(currency)
    text = t("pay_prepay", lang,
             amount=amount1_str,
             currency=currency,
             details=details)

    await call.message.edit_text(
        text,
        reply_markup=pay_kb(order_id, lang),
        parse_mode="HTML"
    )
