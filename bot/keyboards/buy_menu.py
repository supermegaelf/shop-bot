from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from utils import goods
from db.methods import get_user_promo_discount

async def get_buy_menu_keyboard(tg_id: int, months: int, purchase_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    filtered_goods = [good for good in goods.get() if good['months'] == months and good["type"] == purchase_type]
    discount = await get_user_promo_discount(tg_id)

    for good in filtered_goods:
        builder.row(InlineKeyboardButton(
            text=_("{title} – {price_ru} ₽").format(
                title=good['title'],
                price_ru = int(good['price']['ru'] * (1 - discount / 100))
            ) + (f" (-{discount}%)" if discount else ""), 
            callback_data=good['callback'])
        )
    
    back_callback = "back_to_subscription" if purchase_type == "update" else "payment"
    builder.row(InlineKeyboardButton(text=_("button_back"), callback_data=back_callback))
    
    return builder.as_markup()
