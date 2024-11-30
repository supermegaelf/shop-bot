from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("🔌 Can't set up VPN"), callback_data='set_up_problem')
        ],
        [
            InlineKeyboardButton(text=_("⛔️ VPN doesn't work"), callback_data='working_problem')
        ],
        [
            InlineKeyboardButton(text=_("🆘 Contact support"), url=glv.config['SUPPORT_LINK'])
        ],
    ]
   
   return InlineKeyboardMarkup(inline_keyboard=kb)