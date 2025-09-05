# Shop Bot 🚀

Telegram bot for VPN subscription sales with multi-panel support and multiple payment methods.

## ✨ Features

- 🎯 **Multi-Panel Support**: Marzban and Remnawave
- 💳 **Payment Methods**: YooKassa (RUB), Cryptomus (USD), Telegram Stars
- 🆓 **Trial Subscriptions**: Configurable free periods
- 📊 **Traffic Management**: Flexible data limits and top-ups
- 🌍 **Multilingual**: Russian and English

## 🚀 Quick Start

1. **Clone and setup**
```bash
git clone https://github.com/supermegaelf/shop-bot.git
cd shop-bot
cp .env.example .env
cp goods.example.json goods.json
```

2. **Configure**
- Edit `.env` with your bot token and panel settings
- Edit `goods.json` with your subscription plans

3. **Run**
```bash
docker compose up -d
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# MAIN SETTINGS
BOT_TOKEN=12345678910:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq
ADMINS=[123456789, 987654321, 555666777]
SHOP_NAME=My VPN Shop
PROTOCOLS=vless shadowsocks
TEST_PERIOD=true
PERIOD_LIMIT=120
EMAIL=support@example.com
RENEW_NOTIFICATION_TIME="16:00"
EXPIRED_NOTIFICATION_TIME="16:05"

# PANEL CONFIGURATION
PANEL_HOST=http://localhost:8000
PANEL_GLOBAL=
PANEL_USER=admin
PANEL_PASS=your_secure_panel_password
PANEL_TYPE=MARZBAN
WEBHOOK_URL=https://your-bot-domain.com
WEBHOOK_PORT=8777
WEBHOOK_SECRET="your_webhook_secret_key_32chars"

# DATABASE
DB_NAME=shop
DB_USER=shopuser
DB_PASS=secure_db_password_here
DB_ROOT_PASS=secure_root_password_here
DB_ADDRESS=localhost
DB_PORT=3307

# PAYMENT SERVICES
YOOKASSA_TOKEN=test_your_yookassa_token_here
YOOKASSA_SHOPID=123456
CRYPTO_TOKEN=your_cryptomus_api_token_here
MERCHANT_UUID=12345678-1234-1234-1234-123456789abc

# TELEGRAM SETTINGS
TG_INFO_CHANEL=https://t.me/your_info_channel
SUPPORT_LINK=https://t.me/your_support_bot
STARS_PAYMENT_ENABLED=true
ABOUT=https://t.me/your_info_channel/about
UPDATE_GEO_LINK=https://t.me/your_info_channel/geo_update
```

### Products Configuration (goods.json)
```json
[
    {
        "title": "100 GB",
        "type": "renew",
        "price": {
            "en": 2.99,
            "ru": 299,
            "stars": 150
        },
        "callback": "option_1",
        "months": 1,
        "data_limit": 107374182400
    },
    {
        "title": "300 GB",
        "type": "renew",
        "price": {
            "en": 4.99,
            "ru": 499,
            "stars": 250
        },
        "callback": "option_2",
        "months": 1,
        "data_limit": 322122547200
    },
    {
        "title": "100 GB",
        "type": "renew",
        "price": {
            "en": 7.99,
            "ru": 799,
            "stars": 400
        },
        "callback": "option_3",
        "months": 3,
        "data_limit": 107374182400
    },
    {
        "title": "10 GB",
        "type": "update",
        "price": {
            "en": 0.99,
            "ru": 99,
            "stars": 50
        },
        "callback": "option_10",
        "months": 1,
        "data_limit": 10737418240
    },
    {
        "title": "50 GB",
        "type": "update",
        "price": {
            "en": 1.99,
            "ru": 199,
            "stars": 100
        },
        "callback": "option_11",
        "months": 1,
        "data_limit": 53687091200
    }
]
```

### Product Types
- `"type": "renew"` - Full subscription with time extension
- `"type": "update"` - Traffic top-up for existing users

## 📱 Webhooks

Set these URLs in your payment provider dashboards:
- YooKassa: `https://your-domain.com/yookassa_payment`
- Cryptomus: `https://your-domain.com/cryptomus_payment`

## 📄 License

GPL-3.0 License - see [LICENSE](LICENSE) file.

---

⭐ **Star this repository if it helped you!**
