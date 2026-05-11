from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
from translations import t
from keyboards import main_menu_kb, captcha_kb, lang_kb, back_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    db.create_user(user.id, user.username or "", user.full_name or "")
    row = db.get_user(user.id)

    if row and row["is_banned"]:
        await message.answer(t("banned", "ru"))
        return

    if row and row["captcha_passed"]:
        lang = row["language"] if row else "ru"
        await message.answer(
            t("welcome", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML"
        )
    else:
        # Показываем капчу
        await message.answer(
            "🤖 <b>Защита от ботов</b>\n\nСколько будет <b>3 + 5</b>?\n\n"
            "🤖 <b>Bot protection</b>\n\nWhat is <b>3 + 5</b>?",
            reply_markup=captcha_kb(),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("captcha_"))
async def captcha_answer(call: CallbackQuery):
    answer = call.data.split("_")[1]
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    if answer == "8":
        db.set_captcha_passed(call.from_user.id)
        await call.message.edit_text(
            t("welcome", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML"
        )
    else:
        await call.answer("❌ Неверно! Попробуйте ещё раз. / Wrong!", show_alert=True)

@router.callback_query(F.data == "main_menu")
async def main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    try:
        await call.message.edit_text(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML"
        )
    except Exception:
        await call.message.answer(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "choose_lang")
async def choose_lang(call: CallbackQuery):
    await call.message.edit_text(
        "🌐 <b>Выберите язык / Choose language / Оберіть мову</b>",
        reply_markup=lang_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("setlang_"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split("_")[1]
    db.set_user_lang(call.from_user.id, lang)
    row = db.get_user(call.from_user.id)
    await call.answer("✅ OK")
    await call.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "leaders")
async def leaders(call: CallbackQuery):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    top = db.get_top_users(10)
    text = t("leaders_title", lang) + "\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    for i, u in enumerate(top):
        name = u["full_name"] or u["username"] or f"id{u['user_id']}"
        text += f"{medals[i]} {name} — {u['total_orders']} заказов\n"
    if not top:
        text += "Пока нет данных."
    await call.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")

@router.callback_query(F.data == "channel")
async def channel(call: CallbackQuery):
    from config import REVIEWS_CHANNEL
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Перейти в канал / Go to channel", url=REVIEWS_CHANNEL)],
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")],
    ])
    await call.message.edit_text("📢 Канал с отзывами / Reviews channel", reply_markup=kb)
