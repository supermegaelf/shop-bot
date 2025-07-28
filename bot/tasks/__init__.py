import aioschedule
import asyncio
import logging

from .update_token import update_marzban_token

import glv

async def register():
    logging.info('Register cron jobs.')
    
    async def token_update_task():
        await update_marzban_token()
    
    aioschedule.every(5).minutes.do(token_update_task)
    
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
