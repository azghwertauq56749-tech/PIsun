from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from translations import t, LANGS
from data.catalog import BOT_CATALOG, get_bot_name

def main_menu_kb(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 " + ("Каталог" if lang=="ru" else "Catalog" if lang=="en" else "Каталог"),
                              callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 " + ("Корзина" if lang=="ru" else "Cart" if lang=="en" else "Кошик" if lang=="ua" else "Cart"),
                              callback_data="cart")],
        [InlineKeyboardButton(text="🎰 Казино / Casino", callback_data="casino")],
        [InlineKeyboardButton(text="📢 " + ("Канал с отзывами" if lang=="ru" else "Reviews channel"),
                              callback_data="channel")],
        [InlineKeyboardButton(text="🎧 " + ("Поддержка" if lang=="ru" else "Support" if lang=="en" else "Підтримка" if lang=="ua" else "Support"),
                              callback_data="support")],
        [InlineKeyboardButton(text="🏆 " + ("Лидеры" if lang=="ru" else "Leaders" if lang=="en" else "Лідери" if lang=="ua" else "Leaders"),
                              callback_data="leaders")],
        [InlineKeyboardButton(text="🌐 " + ("Язык" if lang=="ru" else "Language" if lang=="en" else "Мова" if lang=="ua" else "Language"),
                              callback_data="choose_lang")],
    ])

def catalog_kb(lang="ru"):
    rows = []
    for i in range(0, len(BOT_CATALOG), 2):
        row = []
        b = BOT_CATALOG[i]
        name = b["emoji"] + " " + get_bot_name(b, lang)[:22]
        row.append(InlineKeyboardButton(text=name, callback_data=f"bot_{b['id']}"))
        if i+1 < len(BOT_CATALOG):
            b2 = BOT_CATALOG[i+1]
            name2 = b2["emoji"] + " " + get_bot_name(b2, lang)[:22]
            row.append(InlineKeyboardButton(text=name2, callback_data=f"bot_{b2['id']}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def currency_kb(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Гривны (UAH)", callback_data="curr_UAH")],
        [InlineKeyboardButton(text="🇺🇸 Доллары (USD)", callback_data="curr_USD")],
        [InlineKeyboardButton(text="🇪🇺 Евро (EUR)",   callback_data="curr_EUR")],
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="catalog")],
    ])

def pay_kb(order_id: int, lang="ru"):
    paid_text = t("paid_btn", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=paid_text, callback_data=f"paid_{order_id}_prepay")],
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")],
    ])

def final_pay_kb(order_id: int, lang="ru"):
    paid_text = t("paid_btn", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=paid_text, callback_data=f"paid_{order_id}_final")],
    ])

def admin_payment_kb(order_id: int, pay_type: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{order_id}_{pay_type}"),
            InlineKeyboardButton(text="❌ Отменить",    callback_data=f"admin_cancel_{order_id}_{pay_type}"),
        ],
        [
            InlineKeyboardButton(text="🚫 Бан пользователя", callback_data=f"admin_ban_{order_id}"),
        ],
    ])

def back_kb(target="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data=target)],
    ])

def lang_kb():
    rows = []
    items = list(LANGS.items())
    for i in range(0, len(items), 3):
        row = []
        for code, name in items[i:i+3]:
            row.append(InlineKeyboardButton(text=name, callback_data=f"setlang_{code}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def captcha_kb():
    """Цифры для капчи (ответ на 3+5=8)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="6", callback_data="captcha_6"),
            InlineKeyboardButton(text="7", callback_data="captcha_7"),
            InlineKeyboardButton(text="8", callback_data="captcha_8"),
            InlineKeyboardButton(text="9", callback_data="captcha_9"),
        ],
    ])

def casino_kb(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Крутить (бесплатно)", callback_data="casino_spin_0")],
        [InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")],
    ])

def cart_kb(orders, lang="ru"):
    rows = []
    for order in orders:
        status_icons = {"new": "🆕", "in_work": "⚙️", "completed": "✅", "cancelled": "❌"}
        icon = status_icons.get(order["status"], "❓")
        rows.append([
            InlineKeyboardButton(
                text=f"{icon} #{order['id']} {order['bot_type'][:20]}",
                callback_data=f"order_detail_{order['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def order_detail_kb(order_id, status, lang="ru"):
    rows = []
    if status == "ready_for_finalpay":
        rows.append([InlineKeyboardButton(
            text="💳 " + ("Оплатить 50%" if lang=="ru" else "Pay 50%"),
            callback_data=f"finalpay_{order_id}"
        )])
    if status not in ("completed", "cancelled"):
        rows.append([InlineKeyboardButton(
            text="❌ " + ("Отменить заказ" if lang=="ru" else "Cancel order"),
            callback_data=f"cancel_order_{order_id}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад / Back", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def deliver_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Установить ссылку доставки", callback_data=f"set_delivery_{order_id}")],
    ])
