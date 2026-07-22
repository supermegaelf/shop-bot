from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
    callback_data = 'payment_from_notification' if from_notification else 'payment'
    
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_renew", lang),
                callback_data=callback_data)
        ]
    ]
    if back:
        kb.append([InlineKeyboardButton(text=get_i18n_string("button_back", lang), callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_install_subscription_keyboard(subscription_url, lang='en') -> InlineKeyboardMarkup:
    kb = []
    if subscription_url:
        kb.append([
            InlineKeyboardButton(
                text=get_i18n_string("button_install", lang),
                url=subscription_url
            )
        ])
    kb.append([
        InlineKeyboardButton(
            text=get_i18n_string("button_dismiss", lang),
            callback_data="dismiss_after_install"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_subscription_details_keyboard(subscription_url: str, lang=None, show_buy_traffic_button: bool = False, show_change_tariff_button: bool = False) -> InlineKeyboardMarkup:
    from aiogram.utils.i18n import gettext as _

    builder = InlineKeyboardBuilder()

    if subscription_url:
        builder.row(
            InlineKeyboardButton(
                text=_("button_install"),
                url=subscription_url
            )
        )

    if show_buy_traffic_button:
        builder.row(
            InlineKeyboardButton(
                text=_("button_buy_more_traffic"),
                callback_data="extend_data_limit"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=_("button_renew"),
            callback_data="payment"
        )
    )

    if show_change_tariff_button:
        builder.row(
            InlineKeyboardButton(
                text=_("button_change_tariff"),
                callback_data="change_tariff"
            )
        )
    
    if subscription_url:
        builder.row(
            InlineKeyboardButton(
                text=_("button_share"),
                callback_data="share_subscription"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=_("button_back"),
            callback_data="back_to_main_menu"
        )
    )
    
    return builder.as_markup()