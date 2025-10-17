from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

def get_pay_keyboard(pay_url, good_callback=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=_("button_pay_action"),
            url=pay_url
        )
    )
    if good_callback:
        builder.row(InlineKeyboardButton(text=_("button_back"), callback_data=f"back_to_payment_{good_callback}"))
    return builder.as_markup()
