from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,  WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string

def get_buy_more_traffic_keyboard(lang, back=True, from_notification=False) -> InlineKeyboardMarkup:
    callback_data = 'extend_data_limit_notification' if from_notification else 'extend_data_limit'

    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_buy_more_traffic", lang),
                callback_data=callback_data)
        ]
    ]
    if back:
        kb.append([InlineKeyboardButton(text=get_i18n_string("button_back", lang), callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_renew_subscription_keyboard(lang, back=True, from_notification=False) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_renew", lang),
                callback_data='payment')
        ]
    ]
    if back:
        kb.append([InlineKeyboardButton(text=get_i18n_string("button_back", lang), callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_install_subscription_keyboard(subscription_url, lang='en') -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_install", lang),
                web_app=WebAppInfo(url=subscription_url)
            )
        ],
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_dismiss", lang),
                callback_data="dismiss_after_install"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_subscription_details_keyboard(subscription_url: str, lang=None) -> InlineKeyboardMarkup:
    from aiogram.utils.i18n import gettext as _
    
    builder = InlineKeyboardBuilder()
    
    if subscription_url:
        builder.row(
            InlineKeyboardButton(
                text=_("button_install"),
                web_app=WebAppInfo(url=subscription_url)
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=_("button_share"),
                switch_inline_query=_("\n\nFollow the link below to install VPN ⬇️\n\n{link}").format(link=subscription_url)
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=_("button_back"),
            callback_data="back_to_main_menu"
        )
    )
    
    return builder.as_markup()