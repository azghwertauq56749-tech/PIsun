import random
from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards import casino_kb, back_kb
from translations import t

router = Router()

SLOTS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣", "🔔"]

def spin_slots():
    return [random.choice(SLOTS) for _ in range(3)]

def evaluate(slots):
    if slots[0] == slots[1] == slots[2]:
        if slots[0] == "💎":
            return "jackpot", "🎉 ДЖЕКПОТ! Скидка 30% на финальную оплату!"
        elif slots[0] == "7️⃣":
            return "big_win", "🎊 БОЛЬШОЙ ВЫИГРЫШ! Скидка 20%!"
        elif slots[0] == "⭐":
            return "win", "⭐ ПОБЕДА! Скидка 15%!"
        else:
            return "small_win", f"✨ Выигрыш! Скидка 10% на финальный платёж!"
    elif slots[0] == slots[1] or slots[1] == slots[2] or slots[0] == slots[2]:
        return "tiny_win", "🍀 Два совпадения! Скидка 5%!"
    else:
        return "lose", "😢 Не повезло... Попробуй ещё раз!"

@router.callback_query(F.data == "casino")
async def show_casino(call: CallbackQuery):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"
    await call.message.edit_text(
        t("casino_title", lang),
        reply_markup=casino_kb(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("casino_spin_"))
async def casino_spin(call: CallbackQuery):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    slots = spin_slots()
    result_type, prize_text = evaluate(slots)
    slots_str = " | ".join(slots)

    db.log_casino(call.from_user.id, 0, result_type, prize_text)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Крутить снова / Spin again", callback_data="casino_spin_0")],
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")],
    ])

    text = (
        f"🎰 <b>КАЗИНО</b>\n\n"
        f"[ {slots_str} ]\n\n"
        f"{prize_text}\n\n"
        f"{'🎁 Покажите скриншот при оплате для получения скидки!' if result_type != 'lose' else ''}"
    )

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
