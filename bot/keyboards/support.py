from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

import glv

def get_support_keyboard(from_profile: bool = False) -> InlineKeyboardMarkup:
    callback_data = 'help_from_profile' if from_profile else 'help'
    kb = [
        [
            InlineKeyboardButton(text=_("button_vpn_not_working"), url=glv.config['VPN_NOT_WORKING_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_other_question"), url=glv.config['SUPPORT_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_back"), callback_data=callback_data)
        ],
    ]
   
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_reach_support_keyboard(from_profile: bool = False) -> InlineKeyboardMarkup:
    callback_data = 'support_from_profile' if from_profile else 'support'
    kb = [
        [
            InlineKeyboardButton(text=_("button_support_failed"), url=glv.config['SUPPORT_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_back"), callback_data=callback_data)
        ],
    ]
   
    return InlineKeyboardMarkup(inline_keyboard=kb)
