from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_payment_keyboard(good) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    yoo = glv.config['YOOKASSA_SHOPID'] and glv.config['YOOKASSA_TOKEN']
    crypt = glv.config['MERCHANT_UUID'] and glv.config['CRYPTO_TOKEN']
    f = yoo or crypt
    if not f:
        builder.row(
            InlineKeyboardButton(
                text="Oh no...",
                callback_data=f"none"
            )
        )
        return builder.as_markup()
    if yoo:
        builder.row(
            InlineKeyboardButton(
                text=_("button_card"),
                callback_data=f"pay_kassa_{good['callback']}"
            )
        )

    tribute_urls = {
        'option_1': 'https://t.me/tribute/app?startapp=syDs',  # 100 ГБ, 1 мес - 290 руб
        'option_2': 'https://t.me/tribute/app?startapp=syFS',  # 300 ГБ, 1 мес - 590 руб
        'option_3': 'https://t.me/tribute/app?startapp=syEm',  # 100 ГБ, 3 мес - 690 руб
        'option_4': 'https://t.me/tribute/app?startapp=syEn',  # 300 ГБ, 3 мес - 1390 руб
        'option_5': 'https://t.me/tribute/app?startapp=syEo',  # 100 ГБ, 6 мес - 1290 руб
        'option_6': 'https://t.me/tribute/app?startapp=syEp',  # 300 ГБ, 6 мес - 2590 руб
    }

    if good['callback'] in tribute_urls:
        builder.row(
            InlineKeyboardButton(
                text=_("button_tribute"),
                url=tribute_urls[good['callback']]
            )
        )
    if crypt:
        builder.row(
            InlineKeyboardButton(
                text=_("button_cryptocurrency"),
                callback_data=f"pay_crypto_{good['callback']}"
            )
        )
    if glv.config['STARS_PAYMENT_ENABLED']:
        builder.row(
            InlineKeyboardButton(
                text=f"Telegram Stars ⭐️",
                callback_data=f"pay_stars_{good['callback']}"
            )
        )
    return builder.as_markup()
