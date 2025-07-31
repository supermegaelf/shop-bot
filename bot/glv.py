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
    'RULES_LINK': os.environ.get('RULES_LINK'),
    'SUPPORT_LINK': os.environ.get('SUPPORT_LINK'),
    'DB_URL': f"mysql+asyncmy://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@{os.environ.get('DB_ADDRESS')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}",
    'YOOKASSA_TOKEN': os.environ.get('YOOKASSA_TOKEN'),
    'YOOKASSA_SHOPID': os.environ.get('YOOKASSA_SHOPID'),
    'EMAIL': os.environ.get('EMAIL'),
    'CRYPTO_TOKEN': os.environ.get('CRYPTO_TOKEN'),
    'MERCHANT_UUID': os.environ.get('MERCHANT_UUID'),
    'TRIBUTE_API_KEY': os.environ.get('TRIBUTE_API_KEY'),
    'TRIBUTE_WEBHOOK_SECRET': os.environ.get('TRIBUTE_WEBHOOK_SECRET'),
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
    'TRIBUTE_WEBHOOK_URL': os.environ.get('TRIBUTE_WEBHOOK_URL'),
    'TRIBUTE_API_KEY': os.environ.get('TRIBUTE_API_KEY'),
    'TRIBUTE_PAYMENT_URL': os.environ.get('TRIBUTE_PAYMENT_URL'),
    'TRIBUTE_SUBSCRIPTION_MAPPING': {
        133142: 'option_1',  # 100 GB, 1 месяц (тест)
        
        # ПОДПИСКИ (type: "renew") - раскомментируйте и добавьте ID:
        # ___: 'option_1',  # 100 GB, 1 месяц - 290 руб
        # ___: 'option_2',  # 300 GB, 1 месяц - 590 руб
        # ___: 'option_3',  # 100 GB, 3 месяца - 690 руб
        # ___: 'option_4',  # 300 GB, 3 месяца - 1390 руб
        # ___: 'option_5',  # 100 GB, 6 месяцев - 1290 руб
        # ___: 'option_6',  # 300 GB, 6 месяцев - 2590 руб
        
        # ДОКУПКА ТРАФИКА (type: "update") - раскомментируйте и добавьте ID:
        # ___: 'option_10', # 10 GB, 1 месяц - 50 руб
        # ___: 'option_11', # 50 GB, 1 месяц - 100 руб
        # ___: 'option_7',  # 100 GB, 1 месяц - 150 руб
        # ___: 'option_12', # 10 GB, 3 месяца - 120 руб
        # ___: 'option_13', # 50 GB, 3 месяца - 240 руб
        # ___: 'option_8',  # 100 GB, 3 месяца - 360 руб
        # ___: 'option_14', # 10 GB, 6 месяцев - 220 руб
        # ___: 'option_15', # 50 GB, 6 месяцев - 450 руб
        # ___: 'option_9',  # 100 GB, 6 месяцев - 670 руб
    },
}

bot: Bot = None
storage = None
dp: Dispatcher = None

