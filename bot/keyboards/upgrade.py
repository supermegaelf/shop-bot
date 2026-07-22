from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from utils import goods


def get_upgrade_menu_keyboard(current: dict, options: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for good in options:
        surcharge = goods.get_upgrade_price(current, good, "ru")
        builder.row(InlineKeyboardButton(
            text=_("{title} – {price_ru} ₽").format(
                title=good["title"],
                price_ru=int(surcharge)
            ),
            callback_data=f"upg_{good['callback']}"
        ))

    builder.row(InlineKeyboardButton(text=_("button_back"), callback_data="back_to_subscription"))

    return builder.as_markup()
