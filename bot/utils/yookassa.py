import asyncio
import functools

from yookassa import Configuration
from yookassa import Payment

from db.methods import add_payment, get_user_promo_discount, PaymentPlatform
from utils import goods
import glv

if glv.config['YOOKASSA_SHOPID'] and glv.config['YOOKASSA_TOKEN']:
    Configuration.configure(glv.config['YOOKASSA_SHOPID'], glv.config['YOOKASSA_TOKEN'])

async def create_payment(tg_id: int, callback: str, lang_code: str) -> dict:
    good = goods.get(callback)
    discount = await get_user_promo_discount(tg_id)
    price = int(good['price']['ru'] * (1 - discount / 100))
    bot_username = (await glv.bot.get_me()).username
    payload = {
        "amount": {
            "value": price,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/{bot_username}"
        },
        "capture": True,
        "description": f"Подписка на сервис {glv.config['SHOP_NAME']}",
        "save_payment_method": False,
        "receipt": {
            "customer": {
                "email": glv.config['EMAIL']
            },
            "items": [
                {
                    "description": f"Подписка на сервис: кол-во месяцев - {good['months']}",
                    "quantity": "1",
                    "amount": {
                        "value": price,
                        "currency": "RUB"
                    },
                    "vat_code": "1"
                },
            ]
        }
    }
    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(None, functools.partial(Payment.create, payload))
    return {
        "url": resp.confirmation.confirmation_url,
        "amount": resp.amount.value,
        "payment_id": resp.id
    }
