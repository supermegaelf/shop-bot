from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

def get_back_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=_("⏪ Back"), callback_data='back')
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard=kb)
