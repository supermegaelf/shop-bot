from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from collections import defaultdict

from utils import goods
from db.methods import get_user_promo_discount

async def get_months_keyboard(tg_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    subscription_opts = [good for good in goods.get() if good["type"] == "renew"]
    month_to_min_price = defaultdict(lambda: float('inf'))
    for good in subscription_opts:
        month_to_min_price[good['months']] = min(month_to_min_price[good['months']], good['price']['ru'])
    discount = await get_user_promo_discount(tg_id)
    for months, price in month_to_min_price.items():
        builder.row(InlineKeyboardButton(
            text=_("button_subscription_months").format(
                months = months,
                price = int(price * (1 - discount / 100))
            ) + (f" (-{discount}%)" if discount else ""), 
            callback_data=f"months_{months}")
        )
    return builder.as_markup()