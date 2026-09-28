import asyncio
import weakref
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

class UserLock(BaseMiddleware):
    def __init__(self):
        self._locks = weakref.WeakValueDictionary()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or (isinstance(event, Update) and event.pre_checkout_query):
            return await handler(event, data)
        lock = self._locks.setdefault(user.id, asyncio.Lock())
        async with lock:
            return await handler(event, data)
