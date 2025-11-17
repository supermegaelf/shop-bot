import asyncio
import logging
from datetime import datetime

from aiogram import Router
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext

from keyboards import get_main_menu_keyboard
from .messages import profile, help
from db.methods import get_promo_code_by_code, has_activated_promo_code, activate_promo_code
from utils import MessageCleanup, MessageType
import glv

router = Router(name="commands-router")

@router.message(
    Command("start")
)
async def start(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    
    state_data = await state.get_data()
    if glv.MESSAGE_CLEANUP_DEBUG:
        logging.info(f"Start command: state data for user {tg_id}: {state_data}")
    
    previous_start_message_id = state_data.get('last_start_message_id')
    if previous_start_message_id:
        try:
            await glv.bot.delete_message(tg_id, previous_start_message_id)
            if glv.MESSAGE_CLEANUP_DEBUG:
                logging.info(f"Deleted previous /start message {previous_start_message_id}")
        except Exception as e:
            if glv.MESSAGE_CLEANUP_DEBUG:
                logging.debug(f"Failed to delete previous /start message: {e}")
    
    await state.update_data(last_start_message_id=message.message_id)
    
    await cleanup.cleanup_all(tg_id)
    
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("promo_"):
        promo_code = args[1].replace("promo_", "").upper()
        promo = await get_promo_code_by_code(promo_code)
        if not promo:
            sent_message = await message.answer(text=_("message_promo_not_found"), reply_markup=get_main_menu_keyboard())
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        if promo.expires_at and promo.expires_at < datetime.now():
            sent_message = await message.answer(text=_("message_promo_expired"), reply_markup=get_main_menu_keyboard())
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        if await has_activated_promo_code(tg_id, promo.id):
            sent_message = await message.answer(text=_("message_promo_already_activated"), reply_markup=get_main_menu_keyboard())
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        try:
            await activate_promo_code(tg_id, promo.id)
            sent_message = await message.answer(text=_("message_promo_activated").format(discount=promo.discount_percent), 
                             reply_markup=get_main_menu_keyboard())
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
        except Exception as e:
            logging.error(f"Failed to activate promo code {promo_code} for user {tg_id}: {e}", exc_info=True)
            sent_message = await message.answer(
                text=_("message_error") + "\n\n" + _("Failed to activate promo code. Please try again or contact support."),
                reply_markup=get_main_menu_keyboard()
            )
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
    else:
        sent_message = await message.answer(_("message_welcome").format(name=message.from_user.first_name), reply_markup=get_main_menu_keyboard())
        await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)

def register_commands(dp: Dispatcher):
    dp.include_router(router)
