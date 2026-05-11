import random
from datetime import datetime
from config import USD_RATE, EUR_RATE

def generate_unique_amount(base_price: float, currency: str) -> str:
    """Генерирует уникальную сумму с рандомными копейками"""
    kopecks = random.randint(1, 99)
    amount = base_price + kopecks / 100
    return f"{amount:.2f}"

def convert_price(price_uah: float, currency: str) -> float:
    """Конвертирует цену из UAH в нужную валюту"""
    if currency == "UAH":
        return price_uah
    elif currency == "USD":
        return round(price_uah / USD_RATE, 2)
    elif currency == "EUR":
        return round(price_uah / EUR_RATE, 2)
    return price_uah

def get_payment_details(currency: str) -> str:
    from config import PAYMENT_CARD_UAH, PAYMENT_CARD_USD, PAYMENT_CARD_EUR
    if currency == "UAH":
        return f"💳 Карта: <code>{PAYMENT_CARD_UAH}</code>"
    elif currency == "USD":
        return f"💳 {PAYMENT_CARD_USD}"
    elif currency == "EUR":
        return f"💳 {PAYMENT_CARD_EUR}"
    return ""

def now_str() -> str:
    """Текущее время с миллисекундами"""
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3]

def now_display() -> str:
    """Для отображения юзеру"""
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")
