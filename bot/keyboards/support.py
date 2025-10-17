from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

import glv

def get_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("button_vpn_setup_issue"), callback_data='set_up_problem')
        ],
        [
            InlineKeyboardButton(text=_("button_vpn_not_working"), url=glv.config['VPN_NOT_WORKING_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_other_question"), url=glv.config['SUPPORT_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_back"), callback_data='help')
        ],
    ]
   
   return InlineKeyboardMarkup(inline_keyboard=kb)

def get_reach_support_keyboard() -> InlineKeyboardMarkup:
   kb = [
        [
            InlineKeyboardButton(text=_("button_support_failed"), url=glv.config['SUPPORT_LINK'])
        ],
        [
            InlineKeyboardButton(text=_("button_back"), callback_data='support')
        ],
    ]
   
   return InlineKeyboardMarkup(inline_keyboard=kb)
