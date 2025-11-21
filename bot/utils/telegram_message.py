from datetime import datetime, timedelta, timezone
import logging
import asyncio

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound
from aiogram.types import Message


async def try_delete_message(message: Message, debug: bool = False) -> bool:
    if message is None:
        if debug:
            logging.warning("try_delete_message: message is None")
        return False
    
    if not hasattr(message, 'message_id') or message.message_id is None:
        if debug:
            logging.warning("try_delete_message: message_id is missing")
        return False
    
    message_date = message.date
    if message_date is not None:
        if message_date.tzinfo is None:
            message_date = message_date.replace(tzinfo=timezone.utc)
        now = datetime.now(message_date.tzinfo)
        age = now - message_date
        if age > timedelta(hours=48):
            if debug:
                logging.warning(f"try_delete_message: message {message.message_id} is too old ({age})")
            return False
    
    try:
        await asyncio.wait_for(message.delete(), timeout=5.0)
        if debug:
            logging.info(f"try_delete_message: successfully deleted message {message.message_id} in chat {message.chat.id}")
        return True
    except asyncio.TimeoutError:
        if debug:
            logging.warning(f"try_delete_message: timeout deleting message {message.message_id}")
        return False
    except TelegramBadRequest as e:
        error_message = str(e).lower()
        if "message to delete not found" in error_message or "message can't be deleted" in error_message:
            if debug:
                logging.debug(f"try_delete_message: message {message.message_id} already deleted or can't be deleted: {e}")
        else:
            if debug:
                logging.warning(f"try_delete_message: TelegramBadRequest for message {message.message_id}: {e}")
        return False
    except TelegramForbiddenError as e:
        if debug:
            logging.warning(f"try_delete_message: bot doesn't have permission to delete message {message.message_id}: {e}")
        return False
    except TelegramNotFound as e:
        if debug:
            logging.debug(f"try_delete_message: message {message.message_id} not found: {e}")
        return False
    except Exception as e:
        if debug:
            logging.error(f"try_delete_message: unexpected error deleting message {message.message_id}: {e}", exc_info=True)
        return False

