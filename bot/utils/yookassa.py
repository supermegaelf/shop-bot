import logging

from yookassa import Configuration
from yookassa import Payment

from db.methods import get_user_promo_discount
from utils import goods
import glv

if glv.config['YOOKASSA_SHOPID'] and glv.config['YOOKASSA_TOKEN']:
    Configuration.configure(glv.config['YOOKASSA_SHOPID'], glv.config['YOOKASSA_TOKEN'])

async def create_payment(tg_id: int, callback: str, lang_code: str) -> dict | None:
    receipt_email = glv.config.get('EMAIL')
    if not receipt_email:
        logging.error("YooKassa receipt email is not configured (EMAIL env var is missing)")
        return None

    good = goods.get(callback)
    discount = await get_user_promo_discount(tg_id)
    price = int(good['price']['ru'] * (1 - discount / 100))
    resp = Payment.create({
        "amount": {
            "value": price,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/{(await glv.bot.get_me()).username}"
        },
        "capture": True,
        "description": f"Подписка на сервис {glv.config['SHOP_NAME']}",
        "save_payment_method": False,
        "receipt": {
            "customer": {
                "email": receipt_email
            },
            "items": [
                {
                    "description": f"Подписка на сервис: кол-во месяцев - {good['months']}",
                    "quantity": "1",
                    "amount": {
                        "value": price,
                        "currency": "RUB"
                    },
                    "vat_code": glv.config.get('YOOKASSA_VAT_CODE', '1'),
                    "payment_mode": glv.config.get('YOOKASSA_PAYMENT_MODE', 'full_prepayment'),
                    "payment_subject": glv.config.get('YOOKASSA_PAYMENT_SUBJECT', 'service'),
                },
            ]
        }
        })
    return {
        "url": resp.confirmation.confirmation_url,
        "amount": resp.amount.value,
        "payment_id": resp.id
    }
