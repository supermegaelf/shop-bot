from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=_("Support ❤️"), callback_data='support'))
    builder.row(InlineKeyboardButton(text=_("Frequent questions 📝"), callback_data='faq'))

    if glv.config['RULES_LINK']:
        builder.row(InlineKeyboardButton(text=_("Terms of service 📃"), url=glv.config['RULES_LINK']))
    else:
        builder.row(InlineKeyboardButton(text=_("Terms of service 📃"), callback_data='tos')) 
         
    return builder.as_markup()

def get_back_to_help_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=_("⏪ Back"), callback_data='back_to_help')
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)
