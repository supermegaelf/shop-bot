from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import goods

def get_month_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    subscription_opts = goods.get()
    month_to_min_price = dict()
    for good in subscription_opts:
        if month_to_min_price[good['months']] is None or int(month_to_min_price[good['months']]) > int(good['price']['ru']):
            month_to_min_price[good['months']] = good['price']['ru']
    for month, price in month_to_min_price:
        builder.row(InlineKeyboardButton(
            text=f"{month} мес. от {price}₽", 
            callback_data=f"month_{month}")
        )
    return builder.as_markup()