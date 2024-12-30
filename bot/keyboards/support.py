from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

import glv

def get_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("Can't set up VPN 🔌"), callback_data='set_up_problem')
        ],
        [
            InlineKeyboardButton(text=_("VPN doesn't work ⛔️"), callback_data='usage_problem')
        ],
        [
            InlineKeyboardButton(text=_("⏪ Back"), callback_data='help')
        ],
    ]
   
   return InlineKeyboardMarkup(inline_keyboard=kb)

def get_reach_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("It didn't work 🆘"), url=glv.config['SUPPORT_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("⏪ Back"), callback_data='support')
        ],
    ]
   
   return InlineKeyboardMarkup(inline_keyboard=kb)