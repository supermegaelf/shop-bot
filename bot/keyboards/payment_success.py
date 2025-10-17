from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_payment_success_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="back_to_main")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
