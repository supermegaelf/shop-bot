from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,  WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv 

def get_user_profile_keyboard(trial_available:bool, subscription_url:str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if trial_available:
        builder.row(
            InlineKeyboardButton(
                text=_("5 days free 🆓"),
                callback_data="trial"
            )
        )
    if subscription_url: 
        builder.row(
            InlineKeyboardButton(
                text=_("Install ⚙️"),
                web_app=WebAppInfo(url=subscription_url)
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=_("Share 🔗"),
                switch_inline_query=_("\n\nGo to the subscription page to connect to the VPN:\n{link}").format(link=subscription_url)
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=_("Pay 💳"),
            callback_data="payment"
        )
    )
    return builder.as_markup()