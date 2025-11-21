from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string
import glv

def get_main_menu_keyboard(user_id: int = None, lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_vpn_access", lang), callback_data="vpn_access")
        ]
    ]

    if user_id and user_id in glv.config['ADMINS']:
        kb.append([
            InlineKeyboardButton(text=get_i18n_str("button_admin_management", lang), callback_data="admin_management")
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
