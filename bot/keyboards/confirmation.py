from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.i18n import gettext as _

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text=_("button_yes")),
            KeyboardButton(text=_("button_no"))
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)   

