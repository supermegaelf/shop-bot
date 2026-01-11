import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, enums, F
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from handlers.commands import register_commands
from handlers.messages import register_messages
from handlers.callbacks import register_callbacks
from handlers.payments import register_payments
from handlers.broadcast import register_broadcast
from handlers.promo_management import register_promo_management
from handlers.referrals import register_referrals
from handlers.admin_referrals import register_admin_referrals
from middlewares.db_check import DBCheck
from app.routes import check_crypto_payment, check_yookassa_payment, notify_user
import glv

glv.bot = Bot(
    glv.config['BOT_TOKEN'],
    default=DefaultBotProperties(parse_mode=enums.ParseMode.HTML)
)
glv.storage = MemoryStorage()
glv.dp = Dispatcher(storage=glv.storage)
app = web.Application()
logging.basicConfig(level=logging.INFO, stream=sys.stdout,  format="%(asctime)s %(levelname)s %(message)s")

async def on_startup(bot: Bot):
    try:
        await bot.set_webhook(f"{glv.config['WEBHOOK_URL']}/webhook")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")
        logging.warning("Bot will continue without webhook update")

def setup_routers():
    glv.dp.message.filter(F.chat.type == "private")
    glv.dp.callback_query.filter(F.message.chat.type == "private")
    
    register_commands(glv.dp)
    register_messages(glv.dp)
    register_callbacks(glv.dp)
    register_payments(glv.dp)
    register_broadcast(glv.dp)
    register_promo_management(glv.dp)
    register_referrals(glv.dp)
    register_admin_referrals(glv.dp)

def setup_middlewares():
    i18n = I18n(path=Path(__file__).parent / 'locales', default_locale='en', domain='bot')
    i18n_middleware = SimpleI18nMiddleware(i18n=i18n)
    i18n_middleware.setup(glv.dp)
    
    db_check = DBCheck()
    glv.dp.update.outer_middleware(db_check)

async def main():
    setup_routers()
    setup_middlewares()
    glv.dp.startup.register(on_startup)

    app.router.add_post("/cryptomus_payment", check_crypto_payment)
    app.router.add_post("/yookassa_payment", check_yookassa_payment)
    app.router.add_post("/notify_user", notify_user)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=glv.dp,
        bot=glv.bot,
    )
    webhook_requests_handler.register(app, path="/webhook")

    setup_application(app, glv.dp, bot=glv.bot)
    await web._run_app(app, host="0.0.0.0", port=glv.config['WEBHOOK_PORT'])

if __name__ == "__main__":
    asyncio.run(main())
