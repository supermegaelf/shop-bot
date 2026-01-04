from enum import Enum
from typing import Optional, List
import logging
import asyncio
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound

from .telegram_message import safe_edit_or_send

from db.methods import (
    save_user_message,
    get_user_messages,
    delete_user_message
)


class MessageType(Enum):
    NAVIGATION = "navigation"
    PROFILE = "profile"
    PAYMENT = "payment"
    SUCCESS = "success"
    NOTIFICATION = "notification"
    IMPORTANT = "important"


class MessageCleanup:
    CLEANUP_RULES = {
        'show_profile': [MessageType.NAVIGATION, MessageType.NOTIFICATION],
        'start_payment': [MessageType.NAVIGATION],
        'payment_success': [MessageType.PAYMENT, MessageType.NAVIGATION],
        'dismiss_notification': [MessageType.NOTIFICATION],
        'navigate': [MessageType.NAVIGATION],
        'back_to_profile': [MessageType.NAVIGATION, MessageType.NOTIFICATION, MessageType.SUCCESS],
    }

    def __init__(self, bot: Bot, state: FSMContext, debug: bool = False):
        self.bot = bot
        self.state = state
        self.debug = debug
        self._tg_id_cache = None

    async def _get_messages_state(self, chat_id: Optional[int] = None) -> dict:
        data = await self.state.get_data()
        messages = data.get('messages')
        
        if messages is None and chat_id is not None:
            try:
                tg_id = await self._get_tg_id(chat_id)
                db_messages = await get_user_messages(tg_id)
                if db_messages and any(db_messages.values()):
                    messages = db_messages
                    await self.state.update_data(messages=messages)
                    if self.debug:
                        msg_count = sum(1 for m in messages.values() if m)
                        logging.info(f"Cleanup: loaded {msg_count} messages from DB for user {tg_id}")
            except Exception as e:
                if self.debug:
                    logging.warning(f"Cleanup: failed to load messages from DB: {e}")
        
        if messages is None:
            messages = {
                'navigation': [],
                'profile': None,
                'payment': None,
                'notification': [],
                'success': None,
                'important': None
            }
        
        return messages

    async def _get_tg_id(self, chat_id: int) -> int:
        if self._tg_id_cache is None:
            try:
                state_data = await self.state.get_data()
                self._tg_id_cache = state_data.get('tg_id') or chat_id
            except Exception:
                self._tg_id_cache = chat_id
        return self._tg_id_cache

    async def _save_messages_state(self, messages: dict):
        await self.state.update_data(messages=messages)

    async def sync_from_db(self, chat_id: int):
        try:
            tg_id = await self._get_tg_id(chat_id)
            db_messages = await get_user_messages(tg_id)
            if db_messages and any(db_messages.values()):
                await self.state.update_data(messages=db_messages)
                if self.debug:
                    msg_count = sum(1 for m in db_messages.values() if m)
                    logging.info(f"Cleanup: synced {msg_count} messages from DB to state for user {tg_id}")
                return True
        except Exception as e:
            if self.debug:
                logging.warning(f"Cleanup: failed to sync from DB: {e}")
        return False

    async def _delete_message(self, chat_id: int, message_id: int, message_type: Optional[str] = None) -> bool:
        if not message_id:
            if self.debug:
                logging.warning(f"Cleanup: message_id is empty for chat {chat_id}")
            return False
        
        if not isinstance(message_id, int) or message_id <= 0:
            if self.debug:
                logging.warning(f"Cleanup: invalid message_id {message_id} for chat {chat_id}")
            return False
        
        deleted_from_telegram = False
        try:
            await asyncio.wait_for(
                self.bot.delete_message(chat_id, message_id),
                timeout=5.0
            )
            deleted_from_telegram = True
            if self.debug:
                logging.info(f"Cleanup: deleted message {message_id} in chat {chat_id}")
        except asyncio.TimeoutError:
            if self.debug:
                logging.warning(f"Cleanup: timeout deleting message {message_id} in chat {chat_id}")
            return False
        except TelegramBadRequest as e:
            error_message = str(e).lower()
            if "message to delete not found" in error_message:
                deleted_from_telegram = True
                if self.debug:
                    logging.debug(f"Cleanup: message {message_id} in chat {chat_id} already deleted")
            elif "message can't be deleted" in error_message:
                if self.debug:
                    logging.debug(f"Cleanup: message {message_id} in chat {chat_id} can't be deleted (too old or no permission)")
            else:
                if self.debug:
                    logging.warning(f"Cleanup: TelegramBadRequest deleting message {message_id} in chat {chat_id}: {e}")
            return False
        except TelegramForbiddenError as e:
            if self.debug:
                logging.warning(f"Cleanup: bot doesn't have permission to delete message {message_id} in chat {chat_id}: {e}")
            return False
        except TelegramNotFound as e:
            deleted_from_telegram = True
            if self.debug:
                logging.debug(f"Cleanup: message {message_id} in chat {chat_id} not found: {e}")
        except Exception as e:
            if self.debug:
                logging.error(f"Cleanup: unexpected error deleting message {message_id} in chat {chat_id}: {e}", exc_info=True)
            return False
        
        if deleted_from_telegram and message_type:
            try:
                tg_id = await self._get_tg_id(chat_id)
                await delete_user_message(tg_id, message_id, message_type)
                if self.debug:
                    logging.info(f"Cleanup: deleted {message_type} message {message_id} from DB for user {tg_id}")
            except Exception as e:
                if self.debug:
                    logging.warning(f"Cleanup: failed to delete message {message_id} from DB: {e}")
        
        return deleted_from_telegram

    async def _delete_messages(self, chat_id: int, message_ids: List[int], message_type: Optional[str] = None):
        if not message_ids:
            return
        
        tasks = [self._delete_message(chat_id, msg_id, message_type) for msg_id in message_ids if msg_id]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def register_message(self, chat_id: int, message_id: int, message_type: MessageType):
        if not message_id or not isinstance(message_id, int) or message_id <= 0:
            if self.debug:
                logging.warning(f"Cleanup: trying to register invalid message_id {message_id} for type {message_type.value}")
            return
        
        messages = await self._get_messages_state(chat_id)
        
        if message_type in [MessageType.NAVIGATION, MessageType.NOTIFICATION]:
            if message_type.value not in messages:
                messages[message_type.value] = []
            if message_id not in messages[message_type.value]:
                messages[message_type.value].append(message_id)
        else:
            messages[message_type.value] = message_id
        
        await self._save_messages_state(messages)
        
        try:
            tg_id = await self._get_tg_id(chat_id)
            await save_user_message(tg_id, message_id, message_type.value)
            if self.debug:
                logging.info(f"Cleanup: saved {message_type.value} message {message_id} to DB for user {tg_id}")
        except Exception as e:
            if self.debug:
                logging.warning(f"Cleanup: failed to save message {message_id} to DB: {e}")
        
        if self.debug:
            logging.info(f"Cleanup: registered {message_type.value} message {message_id} in chat {chat_id}")

    async def cleanup_by_event(self, chat_id: int, event: str, except_message_id: Optional[int] = None):
        if event not in self.CLEANUP_RULES:
            if self.debug:
                logging.warning(f"Cleanup: unknown event '{event}'")
            return
        
        messages = await self._get_messages_state(chat_id)
        if not messages:
            if self.debug:
                logging.debug(f"Cleanup: no messages in state for event '{event}'")
            return
        
        types_to_delete = self.CLEANUP_RULES[event]
        
        if self.debug:
            logging.info(f"Cleanup: event '{event}' - deleting types {[t.value for t in types_to_delete]}" + (f" (except {except_message_id})" if except_message_id else ""))
        
        deleted_count = 0
        for msg_type in types_to_delete:
            type_key = msg_type.value
            
            if type_key not in messages:
                continue
            
            if isinstance(messages[type_key], list):
                if messages[type_key]:
                    message_ids_to_delete = [msg_id for msg_id in messages[type_key] if msg_id != except_message_id] if except_message_id else messages[type_key]
                    if message_ids_to_delete:
                        await self._delete_messages(chat_id, message_ids_to_delete, type_key)
                        deleted_count += len(message_ids_to_delete)
                    messages[type_key] = [msg_id for msg_id in messages[type_key] if msg_id == except_message_id] if except_message_id else []
            elif messages[type_key] is not None:
                if messages[type_key] != except_message_id:
                    if await self._delete_message(chat_id, messages[type_key], type_key):
                        deleted_count += 1
                    messages[type_key] = None
        
        await self._save_messages_state(messages)
        
        if self.debug:
            logging.info(f"Cleanup: event '{event}' - deleted {deleted_count} message(s)")

    async def cleanup_all(self, chat_id: int):
        messages = await self._get_messages_state(chat_id)
        
        if self.debug:
            logging.info(f"Cleanup: cleanup_all called for chat {chat_id}, messages in state: {messages}")
        
        if not messages or all(
            (isinstance(v, list) and not v) or (not isinstance(v, list) and v is None)
            for v in messages.values()
        ):
            if self.debug:
                logging.debug(f"Cleanup: no messages to delete for chat {chat_id}")
            return
        
        deleted_count = 0
        
        for type_key, message_data in messages.items():
            if isinstance(message_data, list):
                if message_data:
                    if self.debug:
                        logging.info(f"Cleanup: deleting {len(message_data)} {type_key} message(s): {message_data}")
                    await self._delete_messages(chat_id, message_data, type_key)
                    deleted_count += len(message_data)
                    messages[type_key] = []
            elif message_data is not None:
                if self.debug:
                    logging.info(f"Cleanup: deleting {type_key} message: {message_data}")
                if await self._delete_message(chat_id, message_data, type_key):
                    deleted_count += 1
                messages[type_key] = None
        
        await self._save_messages_state(messages)
        
        if self.debug:
            logging.info(f"Cleanup: cleanup_all - deleted {deleted_count} message(s) from chat {chat_id}")

    async def send_navigation(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        except_message_id = reuse_message.message_id if reuse_message else None
        await self.cleanup_by_event(chat_id, 'navigate', except_message_id=except_message_id)

        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.NAVIGATION)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.NAVIGATION)
        return msg.message_id

    async def send_profile(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        except_message_id = reuse_message.message_id if reuse_message else None
        await self.cleanup_by_event(chat_id, 'show_profile', except_message_id=except_message_id)

        messages = await self._get_messages_state(chat_id)
        existing_profile = messages.get('profile')
        if existing_profile and (reuse_message is None or existing_profile != reuse_message.message_id):
            await self._delete_message(chat_id, existing_profile, 'profile')
            messages['profile'] = None
            await self._save_messages_state(messages)

        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.PROFILE)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.PROFILE)
        return msg.message_id

    async def send_payment(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        except_message_id = reuse_message.message_id if reuse_message else None
        await self.cleanup_by_event(chat_id, 'start_payment', except_message_id=except_message_id)

        messages = await self._get_messages_state(chat_id)
        existing_payment = messages.get('payment')
        if existing_payment and (reuse_message is None or existing_payment != reuse_message.message_id):
            await self._delete_message(chat_id, existing_payment, 'payment')
            messages['payment'] = None
            await self._save_messages_state(messages)

        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.PAYMENT)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.PAYMENT)
        return msg.message_id

    async def send_success(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        except_message_id = reuse_message.message_id if reuse_message else None
        await self.cleanup_by_event(chat_id, 'payment_success', except_message_id=except_message_id)

        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.SUCCESS)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.SUCCESS)
        return msg.message_id

    async def send_notification(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.NOTIFICATION)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.NOTIFICATION)
        return msg.message_id

    async def send_important(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, reuse_message: Optional[Message] = None, **kwargs) -> int:
        except_message_id = reuse_message.message_id if reuse_message else None
        await self.cleanup_by_event(chat_id, 'payment_success', except_message_id=except_message_id)

        if reuse_message is not None:
            result_message = await safe_edit_or_send(
                reuse_message,
                text=text,
                reply_markup=reply_markup,
                debug=self.debug,
                **kwargs
            )
            if result_message:
                await self.register_message(chat_id, result_message.message_id, MessageType.IMPORTANT)
                return result_message.message_id

        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )

        await self.register_message(chat_id, msg.message_id, MessageType.IMPORTANT)
        return msg.message_id

    async def dismiss_current(self, chat_id: int, message_id: int):
        await self._delete_message(chat_id, message_id, None)

    async def dismiss_notification_by_id(self, chat_id: int, message_id: int):
        messages = await self._get_messages_state(chat_id)
        
        if message_id in messages.get('notification', []):
            await self._delete_message(chat_id, message_id, 'notification')
            messages['notification'].remove(message_id)
            await self._save_messages_state(messages)

    async def back_to_profile(self, chat_id: int, current_message_id: int):
        await self._delete_message(chat_id, current_message_id, None)
        await self.cleanup_by_event(chat_id, 'back_to_profile')
    
    async def cleanup_back_to_profile_except(self, chat_id: int, except_message_id: int):
        messages = await self._get_messages_state(chat_id)
        types_to_cleanup = [MessageType.NAVIGATION, MessageType.NOTIFICATION, MessageType.SUCCESS]
        
        for msg_type in types_to_cleanup:
            type_key = msg_type.value
            if type_key not in messages:
                continue
            
            if isinstance(messages[type_key], list):
                message_ids_to_delete = [msg_id for msg_id in messages[type_key] if msg_id != except_message_id]
                if message_ids_to_delete:
                    await self._delete_messages(chat_id, message_ids_to_delete, type_key)
                messages[type_key] = [msg_id for msg_id in messages[type_key] if msg_id == except_message_id]
            elif messages[type_key] is not None and messages[type_key] != except_message_id:
                await self._delete_message(chat_id, messages[type_key], type_key)
                messages[type_key] = None
        
        await self._save_messages_state(messages)

    async def edit_navigation(self, chat_id: int, message_id: int, text: str, reply_markup: InlineKeyboardMarkup):
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
            await self.register_message(chat_id, message_id, MessageType.NAVIGATION)
            return True
        except TelegramBadRequest:
            await self._delete_message(chat_id, message_id, 'navigation')
            msg = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
            await self.register_message(chat_id, msg.message_id, MessageType.NAVIGATION)
            return False
