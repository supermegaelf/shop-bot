from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,  WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from db.methods import is_trial_available, has_confirmed_payments

async def get_user_profile_keyboard(tg_id: int, show_buy_traffic_button: bool, subscription_url:str) -> InlineKeyboardMarkup:
    trial_available = await is_trial_available(tg_id)
    is_new_user = not await has_confirmed_payments(tg_id)

    builder = InlineKeyboardBuilder()
    if trial_available:
        builder.row(
            InlineKeyboardButton(
                text=_("5 days free 🆓"),
                callback_data="trial"
            )
        )
    if show_buy_traffic_button:
        builder.row(
            InlineKeyboardButton(
                text=_("Buy more traffic ➕"),
                callback_data="extend_data_limit"
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
            text=_("Pay 💳" if trial_available else "Renew 💳"),
            callback_data="payment"
        )
    )

    if is_new_user:
        builder.row(
            InlineKeyboardButton(
                text=_("Promo code 🎁"),
                callback_data="enter_promo"
            )
        )

    return builder.as_markup()