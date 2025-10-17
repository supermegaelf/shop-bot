from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

def get_xtr_pay_keyboard(good_callback=None) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=_('Pay'), pay=True)
    if good_callback:
        builder.row(InlineKeyboardButton(text=_("button_back"), callback_data=f"back_to_payment_{good_callback}"))
    return builder.as_markup()
