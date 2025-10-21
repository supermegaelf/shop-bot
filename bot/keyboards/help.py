from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_help_keyboard(from_profile: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=_("button_support"), callback_data='support'))
    builder.row(InlineKeyboardButton(text=_("button_frequent_questions"), callback_data='faq'))
    
    if from_profile:
        builder.row(InlineKeyboardButton(text=_("button_back"), callback_data='back_to_profile'))
    else:
        builder.row(InlineKeyboardButton(text=_("button_back"), callback_data='back_to_main'))

    return builder.as_markup()

def get_back_to_help_keyboard(from_profile: bool = False) -> InlineKeyboardMarkup:
    callback_data = 'help_from_profile' if from_profile else 'help'
    kb = [
        [
            InlineKeyboardButton(text=_("button_back"), callback_data=callback_data)
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)
