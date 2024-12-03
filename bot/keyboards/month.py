from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from utils import goods

def get_months_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    subscription_opts = goods.get()
    month_to_min_price = dict()

    for good in subscription_opts:
        сurrent_min_price = month_to_min_price.get(good['months'])
        if сurrent_min_price is None or сurrent_min_price > good['price']['ru']:
            month_to_min_price[good['months']] = good['price']['ru']

    for months, price in month_to_min_price.items():
        builder.row(InlineKeyboardButton(
            text=_("{months} months – from {price} ₽").format(
                months=months,
                price=price
            ), 
            callback_data=f"months_{months}")
        )
    return builder.as_markup()