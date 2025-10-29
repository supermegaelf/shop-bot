from enum import Enum
from typing import Optional, List
import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest


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

    async def _get_messages_state(self) -> dict:
        data = await self.state.get_data()
        return data.get('messages', {
            'navigation': [],
            'profile': None,
            'payment': None,
            'notification': [],
            'success': None,
            'important': None
        })

    async def _save_messages_state(self, messages: dict):
        await self.state.update_data(messages=messages)

    async def _delete_message(self, chat_id: int, message_id: int) -> bool:
        if not message_id:
            return False
        try:
            await self.bot.delete_message(chat_id, message_id)
            if self.debug:
                logging.info(f"Cleanup: deleted message {message_id} in chat {chat_id}")
            return True
        except TelegramBadRequest as e:
            if self.debug:
                logging.warning(f"Cleanup: failed to delete message {message_id} in chat {chat_id}: {e}")
            return False
        except Exception as e:
            if self.debug:
                logging.error(f"Cleanup: unexpected error deleting message {message_id} in chat {chat_id}: {e}")
            return False

    async def _delete_messages(self, chat_id: int, message_ids: List[int]):
        for msg_id in message_ids:
            await self._delete_message(chat_id, msg_id)

    async def register_message(self, chat_id: int, message_id: int, message_type: MessageType):
        messages = await self._get_messages_state()
        
        if message_type in [MessageType.NAVIGATION, MessageType.NOTIFICATION]:
            if message_type.value not in messages:
                messages[message_type.value] = []
            if message_id not in messages[message_type.value]:
                messages[message_type.value].append(message_id)
        else:
            messages[message_type.value] = message_id
        
        await self._save_messages_state(messages)
        
        if self.debug:
            logging.info(f"Cleanup: registered {message_type.value} message {message_id}")

    async def cleanup_by_event(self, chat_id: int, event: str):
        if event not in self.CLEANUP_RULES:
            if self.debug:
                logging.warning(f"Cleanup: unknown event '{event}'")
            return
        
        messages = await self._get_messages_state()
        types_to_delete = self.CLEANUP_RULES[event]
        
        if self.debug:
            logging.info(f"Cleanup: event '{event}' - deleting types {[t.value for t in types_to_delete]}")
        
        for msg_type in types_to_delete:
            type_key = msg_type.value
            
            if type_key in messages:
                if isinstance(messages[type_key], list):
                    await self._delete_messages(chat_id, messages[type_key])
                    messages[type_key] = []
                elif messages[type_key] is not None:
                    await self._delete_message(chat_id, messages[type_key])
                    messages[type_key] = None
        
        await self._save_messages_state(messages)

    async def send_navigation(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        await self.cleanup_by_event(chat_id, 'navigate')
        
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.NAVIGATION)
        return msg.message_id

    async def send_profile(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        await self.cleanup_by_event(chat_id, 'show_profile')
        
        messages = await self._get_messages_state()
        if messages.get('profile'):
            await self._delete_message(chat_id, messages['profile'])
        
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.PROFILE)
        return msg.message_id

    async def send_payment(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        await self.cleanup_by_event(chat_id, 'start_payment')
        
        messages = await self._get_messages_state()
        if messages.get('payment'):
            await self._delete_message(chat_id, messages['payment'])
        
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.PAYMENT)
        return msg.message_id

    async def send_success(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        await self.cleanup_by_event(chat_id, 'payment_success')
        
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.SUCCESS)
        return msg.message_id

    async def send_notification(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.NOTIFICATION)
        return msg.message_id

    async def send_important(self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup, **kwargs) -> int:
        await self.cleanup_by_event(chat_id, 'payment_success')
        
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs
        )
        
        await self.register_message(chat_id, msg.message_id, MessageType.IMPORTANT)
        return msg.message_id

    async def dismiss_current(self, chat_id: int, message_id: int):
        await self._delete_message(chat_id, message_id)

    async def dismiss_notification_by_id(self, chat_id: int, message_id: int):
        messages = await self._get_messages_state()
        
        if message_id in messages.get('notification', []):
            await self._delete_message(chat_id, message_id)
            messages['notification'].remove(message_id)
            await self._save_messages_state(messages)

    async def back_to_profile(self, chat_id: int, current_message_id: int):
        await self._delete_message(chat_id, current_message_id)
        await self.cleanup_by_event(chat_id, 'back_to_profile')

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
            await self._delete_message(chat_id, message_id)
            msg = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
            await self.register_message(chat_id, msg.message_id, MessageType.NAVIGATION)
            return False
