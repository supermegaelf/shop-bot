from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,  WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from utils import get_i18n_string
from db.methods import is_trial_available, has_confirmed_payments, get_user_promo_discount

async def get_user_profile_keyboard(tg_id: int, show_buy_traffic_button: bool, subscription_url:str) -> InlineKeyboardMarkup:
    trial_available = await is_trial_available(tg_id)
    is_new_user = not await has_confirmed_payments(tg_id)
    discount = await get_user_promo_discount(tg_id)

    builder = InlineKeyboardBuilder()
    if trial_available:
        builder.row(
            InlineKeyboardButton(
                text=_("button_free_trial"),
                callback_data="trial"
            )
        )
    if show_buy_traffic_button:
        builder.row(
            InlineKeyboardButton(
                text=_("button_buy_more_traffic"),
                callback_data="extend_data_limit"
            )
        )

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
            text=_("button_pay" if trial_available else "button_renew"),
            callback_data="payment"
        )
    )

    if is_new_user and not discount:
        builder.row(
            InlineKeyboardButton(
                text=_("button_promo_code"),
                callback_data="enter_promo"
            )
        )

    return builder.as_markup()

async def get_buy_more_traffic_keyboard(lang) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_buy_more_traffic", lang),
                callback_data='extend_data_limit')
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)

async def get_renew_subscription_keyboard(lang) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=get_i18n_string("button_renew", lang),
                callback_data='payment')
        ]
    ] 
    return InlineKeyboardMarkup(inline_keyboard=kb)