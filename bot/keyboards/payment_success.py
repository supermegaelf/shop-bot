from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import get_i18n_string

def get_payment_success_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_dismiss", lang) if lang else "Dismiss ✖️",
                callback_data="dismiss_payment_success"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
