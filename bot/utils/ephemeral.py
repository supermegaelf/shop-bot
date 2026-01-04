import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound, TelegramServerError, TelegramRetryAfter
from utils.lang import get_i18n_string

class EphemeralNotification:
    
    @staticmethod
    def get_dismiss_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
        dismiss_text = get_i18n_string("button_dismiss", lang)
        kb = [[InlineKeyboardButton(text=dismiss_text, callback_data="dismiss_notification")]]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    @staticmethod
    async def send_ephemeral(
        bot: Bot,
        chat_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        lang: str = 'en',
        **kwargs
    ) -> Optional[int]:
        try:
            if reply_markup is None:
                reply_markup = EphemeralNotification.get_dismiss_keyboard(lang)
            else:
                existing_buttons = reply_markup.inline_keyboard
                dismiss_text = get_i18n_string("button_dismiss", lang)
                dismiss_button = [InlineKeyboardButton(
                    text=dismiss_text,
                    callback_data="dismiss_notification"
                )]
                new_buttons = existing_buttons + [dismiss_button]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
            
            msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                **kwargs
            )
            
            return msg.message_id
            
        except TelegramBadRequest as e:
            error_message = str(e).lower()
            if "chat not found" in error_message or "user not found" in error_message:
                logging.debug(f"Failed to send ephemeral notification to {chat_id}: {e}")
            else:
                logging.warning(f"Failed to send ephemeral notification to {chat_id}: {e}")
            return None
        except TelegramForbiddenError as e:
            logging.warning(f"Bot doesn't have permission to send ephemeral notification to {chat_id}: {e}")
            return None
        except TelegramNotFound as e:
            logging.debug(f"Chat {chat_id} not found for ephemeral notification: {e}")
            return None
        except (TelegramServerError, TelegramRetryAfter) as e:
            logging.warning(f"Telegram server error sending ephemeral notification to {chat_id}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error sending ephemeral notification to {chat_id}: {e}", exc_info=True)
            return None
