import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import get_i18n_string


def get_payment_success_keyboard(
    lang=None, from_notification=False
) -> InlineKeyboardMarkup:
    callback_data = (
        "dismiss_payment_success_notification"
        if from_notification
        else "dismiss_payment_success"
    )

    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_back", lang) if lang else "⬅️ Back",
                callback_data=callback_data,
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
