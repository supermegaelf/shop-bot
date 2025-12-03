import os
import json

from aiogram import Bot, Dispatcher

def _parse_admins(admins_str: str) -> list:
    if not admins_str:
        return []
    
    admins_str = admins_str.strip()
    
    if admins_str.startswith('[') and admins_str.endswith(']'):
        try:
            parsed = json.loads(admins_str)
            if isinstance(parsed, list):
                result = []
                for admin_id in parsed:
                    try:
                        result.append(int(admin_id))
                    except (ValueError, TypeError):
                        continue
                return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    
    admins_list = []
    for admin_id in admins_str.split(','):
        admin_id = admin_id.strip()
        if admin_id:
            try:
                admins_list.append(int(admin_id))
            except ValueError:
                continue
    
    return admins_list

config = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'SHOP_NAME': os.environ.get('SHOP_NAME'),
    'PERIOD_LIMIT': int(os.environ.get('PERIOD_LIMIT', 72)),
    'SUPPORT_LINK': os.environ.get('SUPPORT_LINK'),
    'DB_URL': f"mysql+asyncmy://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@{os.environ.get('DB_ADDRESS')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}",
    'YOOKASSA_TOKEN': os.environ.get('YOOKASSA_TOKEN'),
    'YOOKASSA_SHOPID': os.environ.get('YOOKASSA_SHOPID'),
    'EMAIL': os.environ.get('EMAIL'),
    'CRYPTO_TOKEN': os.environ.get('CRYPTO_TOKEN'),
    'MERCHANT_UUID': os.environ.get('MERCHANT_UUID'),
    'CRYPTO_PAYMENT_ENABLED': os.environ.get('CRYPTO_PAYMENT_ENABLED', False) == 'true',
    'PANEL_HOST': os.environ.get('PANEL_HOST'),
    'REMNAWAVE_TOKEN': os.environ.get('REMNAWAVE_TOKEN'),
    'WEBHOOK_URL': os.environ.get('WEBHOOK_URL'),
    'WEBHOOK_PORT': int(os.environ.get('WEBHOOK_PORT')),
    'WEBHOOK_SECRET': os.environ.get('WEBHOOK_SECRET'),
    'TG_INFO_CHANEL': os.environ.get('TG_INFO_CHANEL'),
    'STARS_PAYMENT_ENABLED': os.environ.get('STARS_PAYMENT_ENABLED', False) == 'true',
    'ADMINS': _parse_admins(os.environ.get('ADMINS', '')),
    'VPN_NOT_WORKING_LINK': os.environ.get('VPN_NOT_WORKING_LINK')
}

bot: Bot = None
storage = None
dp: Dispatcher = None
MESSAGE_CLEANUP_DEBUG = os.environ.get('MESSAGE_CLEANUP_DEBUG', 'false') == 'true'
