from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=_("⏪ Back"), callback_data=callback_data)
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)