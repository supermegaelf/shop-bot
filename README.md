# Shop Bot

Telegram bot for VPN subscription sales with Remnawave panel support and multiple payment methods.

## Features

- 🎯 **Remnawave Panel Support**: Full integration with Remnawave VPN panel
- 💳 **Payment Methods**: YooKassa (RUB), Cryptomus (USD), Telegram Stars
- 🆓 **Trial Subscriptions**: Configurable free periods
- 📊 **Traffic Management**: Flexible data limits and top-ups
- 🌍 **Multilingual**: Russian and English

## Quick Start

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

## Configuration

### `.env` Configuration
```env
# MAIN SETTINGS
BOT_TOKEN=12345678910:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq
ADMINS=[1234567890, 09876543210]
SHOP_NAME=Some VPN
PERIOD_LIMIT=120
EMAIL=forever@queenvpn.com
SUPPORT_LINK=https://t.me/example

# PANEL CONFIGURATION
PANEL_HOST=http://remnawave:3000
REMNAWAVE_TOKEN=your_api_token
WEBHOOK_URL=https://bot.example.com
WEBHOOK_PORT=8777
WEBHOOK_SECRET=your_webhook_secret

# DATABASE
DB_NAME=shop
DB_USER=remnawave
DB_PASS=some_password
DB_ROOT_PASS=some_root_password
DB_ADDRESS=db
DB_PORT=3306

# PAYMENT SERVICES
YOOKASSA_TOKEN=test_K7mP9xR2vL8fT5nJ3wY6aE1cH4uQdZ9oB2gF5iNsWqX
YOOKASSA_SHOPID=123456
CRYPTO_TOKEN=Gf5Kp9wZ2mNv4Qx8cT1rYh7uLjB6aE0dFs3iO9pR5tWqX2nJ8vC4yU6kM1zA7bH3eD9sL5oI8gF2rT6wY4xP0cV7nQ1mJ9uB5aK3hL8tR2fW6eZ4iO1nX7qP5vC9dY8uG3mA6bJ0kL4w
MERCHANT_UUID=8f3c9a1b-2d74-4e6b-b8a5-c17e90f56a3d
STARS_PAYMENT_ENABLED=true
CRYPTO_PAYMENT_ENABLED=false

# TELEGRAM SETTINGS
TG_INFO_CHANEL=https://t.me/example
VPN_NOT_WORKING_LINK=https://t.me/example
```

### Products goods.json
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

## Webhooks

Set these URLs in your payment provider dashboards:
- YooKassa: `https://your-domain.com/yookassa_payment`
- Cryptomus: `https://your-domain.com/cryptomus_payment`

## License

GPL-3.0 License - see [LICENSE](LICENSE) file.

---

⭐ **Star this repository if it helped you!**
