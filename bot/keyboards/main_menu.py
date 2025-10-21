from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_main_menu_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_vpn_access", lang), callback_data="vpn_access")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
