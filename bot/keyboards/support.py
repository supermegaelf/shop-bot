from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("🔌 Can't set up VPN"), callback_data='setup_problem')
        ],
        [
            InlineKeyboardButton(text=_("⛔️ VPN doesn't work"), callback_data='work_problem')
        ],
        [
            InlineKeyboardButton(text=_("🆘 Contact support"), url=glv.config['SUPPORT_LINK'])
        ],
    ]
   
   if glv.config['RULES_LINK']:
      kb.append([])
   return InlineKeyboardMarkup(inline_keyboard=kb)