from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_payment_menu(good) -> tuple[str, InlineKeyboardMarkup]:
    builder = InlineKeyboardBuilder()
    yoo = glv.config['YOOKASSA_SHOPID'] and glv.config['YOOKASSA_TOKEN']
    crypt = glv.config['MERCHANT_UUID'] and glv.config['CRYPTO_TOKEN'] and glv.config['CRYPTO_PAYMENT_ENABLED']
    stars = glv.config['STARS_PAYMENT_ENABLED']
    if yoo:
        builder.row(
            InlineKeyboardButton(
                text=_("button_card"),
                callback_data=f"pay_kassa_{good['callback']}"
            )
        )
    if crypt:
        builder.row(
            InlineKeyboardButton(
                text=_("button_cryptocurrency"),
                callback_data=f"pay_crypto_{good['callback']}"
            )
        )
   
    if stars:
        builder.row(
            InlineKeyboardButton(
                text=f"Telegram Stars ⭐️",
                callback_data=f"pay_stars_{good['callback']}"
            )
        )
    
    if yoo or crypt or stars:
        text = _("message_select_payment_method")
    else:
        text = _("message_payment_methods_unavailable").format(
            link=escape(glv.config["SUPPORT_LINK"], quote=True)
        )

    builder.row(InlineKeyboardButton(text=_("button_back"), callback_data=f"back_to_traffic_{good['type']}_{good['months']}"))
    
    return text, builder.as_markup()
