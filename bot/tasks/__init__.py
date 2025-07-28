import aioschedule
import asyncio
import logging

from .update_token import update_token
from .notify_renew_subscription import notify_users_to_renew_sub
from .notify_expired_sub import notify_users_about_expired_sub

import glv

async def register():
    logging.info('Register cron jobs.')
    aioschedule.every(5).minutes.do(update_token)
    if (glv.config['RENEW_NOTIFICATION_TIME']):
      aioschedule.every().day.at(glv.config['RENEW_NOTIFICATION_TIME']).do(notify_users_to_renew_sub)
    if (glv.config['EXPIRED_NOTIFICATION_TIME']):
      aioschedule.every().day.at(glv.config['EXPIRED_NOTIFICATION_TIME']).do(notify_users_about_expired_sub)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
