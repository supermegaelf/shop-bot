from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
import logging

from utils import goods

def get_buy_menu_keyboard(months) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    logging.info(months)
    subscription_opts = list(filter(lambda good: good['months'] == months, goods.get()))
    logging.info(subscription_opts)
    for good in subscription_opts:
        builder.row(InlineKeyboardButton(
            text=_("{title} - {price_ru}₽").format(
                title=good['title'],
                price_ru=good['price']['ru']
            ), 
            callback_data=good['callback'])
        )
    return builder.as_markup()
