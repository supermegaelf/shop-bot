from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=_("button_support"), callback_data='support'))
    builder.row(InlineKeyboardButton(text=_("button_frequent_questions"), callback_data='faq'))

    # if glv.config['RULES_LINK']:
    #     builder.row(InlineKeyboardButton(text=_("button_terms_of_service"), url=glv.config['RULES_LINK']))
    # else:
    #     builder.row(InlineKeyboardButton(text=_("button_terms_of_service"), callback_data='tos')) 
         
    return builder.as_markup()

def get_back_to_help_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=_("button_back"), callback_data='help')
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)
