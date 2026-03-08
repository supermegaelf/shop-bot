from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_admin_management_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_broadcast", lang), callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("button_promo_codes", lang), callback_data="admin_promo_codes")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("main_menu_referral", lang), callback_data="admin_referrals")
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

def get_promo_codes_management_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_add_promo", lang), callback_data="admin_add_promo")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("button_delete_promo", lang), callback_data="admin_delete_promo")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("button_active_promos", lang), callback_data="admin_active_promos")
        ],
        [
            InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="admin_management")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_promo_delete_keyboard(promo_codes, lang=None) -> InlineKeyboardMarkup:
    kb = []
    for promo in promo_codes:
        kb.append([
            InlineKeyboardButton(
                text=f"{promo.code} ({promo.discount_percent}%)",
                callback_data=f"delete_promo_{promo.id}"
            )
        ])
    kb.append([
        InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="admin_promo_codes")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_promo_back_keyboard(lang=None) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=get_i18n_str("button_back", lang), callback_data="admin_promo_codes")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
