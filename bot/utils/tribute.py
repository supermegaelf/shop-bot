import aiohttp
import json
import logging
from datetime import datetime, timedelta

from db.methods import add_payment, get_user_promo_discount, PaymentPlatform
from utils import goods
import glv

TRIBUTE_API_BASE = "https://tribute.tg/api/v1"

async def create_payment(tg_id: int, callback: str, lang_code: str) -> dict:
    if not glv.config.get('TRIBUTE_API_KEY'):
        raise Exception("TRIBUTE_API_KEY not configured")
    
    good = goods.get(callback)
    discount = await get_user_promo_discount(tg_id)
    
    if lang_code == 'ru':
        price = int(good['price']['ru'] * (1 - discount / 100))
        currency = "RUB"
    else:
        price_usd = good['price']['en'] * (1 - discount / 100)
        price = int(price_usd * 0.92)
        currency = "EUR"
    
    order_data = {
        "title": good['title'],
        "description": f"VPN subscription - {good['title']} for {good['months']} month(s)",
        "amount": price,
        "currency": currency,
        "callback_data": callback,
        "user_id": str(tg_id),
        "webhook_url": f"{glv.config['WEBHOOK_URL']}/tribute_payment"
    }
    
    headers = {
        'Api-Key': glv.config['TRIBUTE_API_KEY'],
        'Content-Type': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{TRIBUTE_API_BASE}/orders", 
                json=order_data, 
                headers=headers
            ) as resp:
                if 200 <= resp.status < 300:
                    response = await resp.json()
                    logging.info(f"Tribute order created: {response}")
                    
                    payment_id = response.get('id') or response.get('order_id')
                    await add_payment(tg_id, callback, lang_code, payment_id, PaymentPlatform.TRIBUTE)
                    
                    return {
                        "url": response.get('payment_url') or response.get('url'),
                        "amount": price,
                        "currency": currency,
                        "order_id": payment_id
                    }
                else:
                    error_text = await resp.text()
                    logging.error(f"Tribute API error {resp.status}: {error_text}")
                    raise Exception(f"Tribute API error: {resp.status} - {error_text}")
                    
    except Exception as e:
        logging.error(f"Failed to create Tribute payment: {e}")
        raise

async def get_order_status(order_id: str) -> dict:
    if not glv.config.get('TRIBUTE_API_KEY'):
        raise Exception("TRIBUTE_API_KEY not configured")
    
    headers = {
        'Api-Key': glv.config['TRIBUTE_API_KEY'],
        'Content-Type': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{TRIBUTE_API_BASE}/orders/{order_id}", 
                headers=headers
            ) as resp:
                if 200 <= resp.status < 300:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logging.error(f"Tribute API error {resp.status}: {error_text}")
                    raise Exception(f"Tribute API error: {resp.status}")
                    
    except Exception as e:
        logging.error(f"Failed to get Tribute order status: {e}")
        raise

async def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    import hmac
    import hashlib
    
    if not glv.config.get('TRIBUTE_WEBHOOK_SECRET'):
        logging.warning("TRIBUTE_WEBHOOK_SECRET not set, skipping signature verification")
        return True
    
    expected_signature = hmac.new(
        glv.config['TRIBUTE_WEBHOOK_SECRET'].encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)