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

## ⚙️ Key Configuration

### Required Settings
```env
BOT_TOKEN=your_telegram_bot_token
PANEL_HOST=http://localhost:8000
PANEL_USER=admin
PANEL_PASS=your_password
WEBHOOK_URL=https://your-domain.com
```

### Payment Setup
```env
# YooKassa
YOOKASSA_TOKEN=your_token
YOOKASSA_SHOPID=your_shop_id

# Cryptomus  
CRYPTO_TOKEN=your_token
MERCHANT_UUID=your_uuid

# Telegram Stars
STARS_PAYMENT_ENABLED=true
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

## 🆘 Support

- 🐛 [Issues](https://github.com/supermegaelf/shop-bot/issues)
- 📖 [Documentation](https://github.com/supermegaelf/shop-bot/wiki)

---

⭐ **Star this repository if it helped you!**
