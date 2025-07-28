import asyncio
import logging
from datetime import datetime, timedelta

from .update_token import update_marzban_token

import glv

async def register():
    logging.info('Register cron jobs.')
    
    last_token_update = datetime.now()
    
    while True:
        try:
            now = datetime.now()
            
            if now - last_token_update >= timedelta(minutes=5):
                logging.info('Running token update task.')
                update_marzban_token()
                last_token_update = now
                
        except Exception as e:
            logging.error(f'Error in scheduled task: {e}')
            
        await asyncio.sleep(60)
