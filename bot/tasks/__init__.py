import aioschedule
import asyncio
import logging

from .update_token import update_marzban_token

async def register_marzban_token_update_task():
    logging.info('Register update Marzban token task.')

    def wrapped_task():
        asyncio.create_task(update_marzban_token())
    
    aioschedule.every(5).minutes.do(wrapped_task)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)