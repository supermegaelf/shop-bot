from datetime import datetime, timedelta, timezone
import logging
import asyncio
from typing import Optional

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound, TelegramServerError, TelegramRetryAfter
from aiogram.types import Message, InlineKeyboardMarkup


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


async def safe_edit_or_send(
    message: Optional[Message],
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: Optional[bool] = None,
    debug: bool = False,
    **kwargs
) -> Optional[Message]:
    if message is None:
        if debug:
            logging.warning("safe_edit_or_send: message is None, cannot edit")
        return None
    
    if not hasattr(message, 'message_id') or message.message_id is None:
        if debug:
            logging.warning("safe_edit_or_send: message_id is missing")
        return None
    
    edit_kwargs = {
        "text": text,
        "reply_markup": reply_markup,
        **kwargs
    }
    if parse_mode is not None:
        edit_kwargs["parse_mode"] = parse_mode
    if disable_web_page_preview is not None:
        edit_kwargs["disable_web_page_preview"] = disable_web_page_preview
    
    try:
        await message.edit_text(**edit_kwargs)
        if debug:
            logging.info(f"safe_edit_or_send: successfully edited message {message.message_id} in chat {message.chat.id}")
        return message
    except TelegramBadRequest as e:
        error_message = str(e).lower()
        if debug:
            if "message to edit not found" in error_message:
                logging.debug(f"safe_edit_or_send: message {message.message_id} not found, will send new")
            elif "message can't be edited" in error_message:
                logging.debug(f"safe_edit_or_send: message {message.message_id} can't be edited (too old or no permission), will send new")
            elif "message is not modified" in error_message:
                logging.debug(f"safe_edit_or_send: message {message.message_id} not modified (same content)")
                return message
            else:
                logging.warning(f"safe_edit_or_send: TelegramBadRequest editing message {message.message_id}: {e}")
    except TelegramForbiddenError as e:
        if debug:
            logging.warning(f"safe_edit_or_send: bot doesn't have permission to edit message {message.message_id}: {e}")
    except TelegramNotFound as e:
        if debug:
            logging.debug(f"safe_edit_or_send: message {message.message_id} not found: {e}")
    except (TelegramServerError, TelegramRetryAfter) as e:
        if debug:
            logging.warning(f"safe_edit_or_send: Telegram server error editing message {message.message_id}: {e}")
    except Exception as e:
        if debug:
            logging.error(f"safe_edit_or_send: unexpected error editing message {message.message_id}: {e}", exc_info=True)
    
    try:
        answer_kwargs = {
            "text": text,
            "reply_markup": reply_markup,
            **kwargs
        }
        if parse_mode is not None:
            answer_kwargs["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            answer_kwargs["disable_web_page_preview"] = disable_web_page_preview
        
        new_message = await message.answer(**answer_kwargs)
        if debug:
            logging.info(f"safe_edit_or_send: sent new message {new_message.message_id} instead of editing {message.message_id}")
        return new_message
    except Exception as e:
        if debug:
            logging.error(f"safe_edit_or_send: failed to send new message after edit failed: {e}", exc_info=True)
        return None

