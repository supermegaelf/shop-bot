from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string
from db.methods import get_user_promo_discount, is_trial_available
import glv

async def get_main_menu_keyboard(user_id: int = None, lang=None, has_subscription: bool = False) -> InlineKeyboardMarkup:
    kb = []
    
    if has_subscription:
        kb.append([
            InlineKeyboardButton(text=get_i18n_str("button_subscription", lang), callback_data="subscription_details")
        ])
    else:
        trial_available = False
        if user_id:
            trial_available = await is_trial_available(user_id)
        
        if trial_available:
            kb.append([
                InlineKeyboardButton(text=get_i18n_str("button_free_trial", lang), callback_data="trial")
            ])
    
    discount = None
    if user_id:
        discount = await get_user_promo_discount(user_id)
    
    if not discount:
        kb.append([
            InlineKeyboardButton(text=get_i18n_str("button_promo_code", lang), callback_data="enter_promo")
        ])
    
    kb.append([
        InlineKeyboardButton(text=get_i18n_str("button_help", lang), callback_data="help")
    ])
    
    if user_id:
        admins = glv.config.get('ADMINS', [])
        if admins and user_id in admins:
            kb.append([
                InlineKeyboardButton(text=get_i18n_str("button_admin_management", lang), callback_data="admin_management")
            ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_i18n_str(text: str, lang = None):
    if lang is None:
        return _(text)
    return get_i18n_string(text, lang)
