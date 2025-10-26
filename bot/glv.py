import os
import json

from aiogram import Bot, Dispatcher

config = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'SHOP_NAME': os.environ.get('SHOP_NAME'),
    'PROTOCOLS': os.environ.get('PROTOCOLS', 'vless').split(),
    'TEST_PERIOD': os.environ.get('TEST_PERIOD', False) == 'true',
    'PERIOD_LIMIT': int(os.environ.get('PERIOD_LIMIT', 72)),
    'ABOUT': os.environ.get('ABOUT'),
    'SUPPORT_LINK': os.environ.get('SUPPORT_LINK'),
    'DB_URL': f"mysql+asyncmy://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@{os.environ.get('DB_ADDRESS')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}",
    'YOOKASSA_TOKEN': os.environ.get('YOOKASSA_TOKEN'),
    'YOOKASSA_SHOPID': os.environ.get('YOOKASSA_SHOPID'),
    'EMAIL': os.environ.get('EMAIL'),
    'CRYPTO_TOKEN': os.environ.get('CRYPTO_TOKEN'),
    'MERCHANT_UUID': os.environ.get('MERCHANT_UUID'),
    'CRYPTO_PAYMENT_ENABLED': os.environ.get('CRYPTO_PAYMENT_ENABLED', False) == 'true',
    'PANEL_HOST': os.environ.get('PANEL_HOST'),
    'PANEL_GLOBAL': os.environ.get('PANEL_GLOBAL'),
    'PANEL_USER': os.environ.get('PANEL_USER'),
    'PANEL_PASS': os.environ.get('PANEL_PASS'),
    'PANEL_TYPE': os.environ.get('PANEL_TYPE', 'MARZBAN'),
    'REMNAWAVE_TOKEN': os.environ.get('REMNAWAVE_TOKEN'),
    'WEBHOOK_URL': os.environ.get('WEBHOOK_URL'),
    'WEBHOOK_PORT': int(os.environ.get('WEBHOOK_PORT')),
    'WEBHOOK_SECRET': os.environ.get('WEBHOOK_SECRET'),
    'TG_INFO_CHANEL': os.environ.get('TG_INFO_CHANEL'),
    'STARS_PAYMENT_ENABLED': os.environ.get('STARS_PAYMENT_ENABLED', False) == 'true',
    'UPDATE_GEO_LINK': os.environ.get('UPDATE_GEO_LINK'),
    'ADMINS': json.loads(os.environ.get('ADMINS', '[]')),
    'VPN_NOT_WORKING_LINK': os.environ.get('VPN_NOT_WORKING_LINK')
}

bot: Bot = None
storage = None
dp: Dispatcher = None
