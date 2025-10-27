import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import get_i18n_string

def get_payment_success_keyboard(lang=None, from_notification=False) -> InlineKeyboardMarkup:

    callback_data = "dismiss_payment_success_notification" if from_notification else "dismiss_payment_success"
    
    logging.info(f"Creating payment_success_keyboard: from_notification={from_notification}, callback_data={callback_data}")
    
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_dismiss", lang) if lang else "Dismiss ✖️",
                callback_data=callback_data
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
