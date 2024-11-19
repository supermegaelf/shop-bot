from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_main_menu_keyboard(lang=None) -> ReplyKeyboardMarkup:
    
    kb = [
        [
            KeyboardButton(text=get_i18n_str("Access to VPN 🏄🏻‍♂️", lang)),
            KeyboardButton(text=get_i18n_str("Help 🕊", lang))
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)   

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
