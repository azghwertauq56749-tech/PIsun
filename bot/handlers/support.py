from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards import back_kb
from translations import t
import logging

router = Router()
logger = logging.getLogger(__name__)

class SupportState(StatesGroup):
    waiting_message = State()

@router.callback_query(F.data == "support")
async def show_support(call: CallbackQuery, state: FSMContext):
    row = db.get_user(call.from_user.id)
    lang = row["language"] if row else "ru"

    await state.set_state(SupportState.waiting_message)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена / Cancel", callback_data="cancel_support")],
    ])
    await call.message.edit_text(
        t("support_msg", lang),
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cancel_support")
async def cancel_support(call: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_menu
    await main_menu(call)

@router.message(SupportState.waiting_message)
async def got_support_msg(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    row = db.get_user(message.from_user.id)
    lang = row["language"] if row else "ru"

    admin_text = (
        f"🎧 <b>Новое сообщение в поддержку</b>\n\n"
        f"👤 {message.from_user.full_name} (@{message.from_user.username or 'нет'})\n"
        f"🆔 <code>{message.from_user.id}</code>\n\n"
        f"💬 {message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="↩️ Ответить",
                    url=f"tg://user?id={message.from_user.id}"
                )],
            ])
            await bot.send_message(admin_id, admin_text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.error(e)

    await message.answer(
        "✅ Сообщение отправлено! Мы ответим как можно скорее.\n"
        "✅ Message sent! We'll reply ASAP.",
        reply_markup=back_kb()
    )
