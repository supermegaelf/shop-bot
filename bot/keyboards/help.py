from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

import glv

def get_help_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("Frequent questions 📝"), callback_data='faq')
        ],
        [
            InlineKeyboardButton(text=_("Terms of service 📃"), callback_data='tos')
        ],
        [
            InlineKeyboardButton(text=_("Support ❤️"), url=glv.config['SUPPORT_LINK'])
        ],
    ]
   return InlineKeyboardMarkup(inline_keyboard=kb)