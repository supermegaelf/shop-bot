from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_admin_management_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_broadcast", lang), callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="back_to_profile")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_broadcast_start_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="admin_management")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_broadcast_confirmation_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_yes", lang), callback_data="broadcast_confirm_yes"),
            InlineKeyboardButton(text=get_i18n_str("button_no", lang), callback_data="broadcast_confirm_no")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
