from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from collections import defaultdict

from utils import goods

def get_months_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    subscription_opts = [good for good in goods.get() if good["type"] == "renew"]
    month_to_min_price = defaultdict(lambda: float('inf'))

    for good in subscription_opts:
        month_to_min_price[good['months']] = min(month_to_min_price[good['months']], good['price']['ru'])

    for months, price in month_to_min_price.items():
        builder.row(InlineKeyboardButton(
            text=_("{months} months – from {price} ₽").format(
                months=months,
                price=price
            ), 
            callback_data=f"months_{months}")
        )
    return builder.as_markup()