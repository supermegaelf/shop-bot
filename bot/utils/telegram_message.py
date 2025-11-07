from datetime import datetime, timedelta, timezone

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def try_delete_message(message: Message) -> bool:
    if message is None:
        return False
    message_date = message.date
    if message_date is not None:
        if message_date.tzinfo is None:
            message_date = message_date.replace(tzinfo=timezone.utc)
        now = datetime.now(message_date.tzinfo)
        if now - message_date > timedelta(hours=48):
            return False
    try:
        await message.delete()
        return True
    except TelegramBadRequest:
        return False
    except Exception:
        return False

