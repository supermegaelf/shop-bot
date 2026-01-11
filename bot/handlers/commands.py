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
from .callbacks import _build_and_send_profile
from db.methods import get_promo_code_by_code, has_activated_promo_code, activate_promo_code, create_vpn_user, get_vpn_user
from utils import MessageCleanup, MessageType, referrals
from panel import get_panel
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
    
    user = await get_vpn_user(tg_id)
    is_new_user = user is None
    
    await create_vpn_user(tg_id)
    
    await referrals.ensure_referral_code(tg_id)
    
    try:
        user = await get_vpn_user(tg_id)
        if user:
            panel = get_panel()
            await panel.update_user_telegram_id(user.vpn_id, tg_id)
    except Exception as e:
        logging.debug(f"Failed to update telegram_id for user {tg_id} in Remnawave: {e}")
    
    args = message.text.split()
    
    logging.info(f"Start command from user {tg_id}, is_new_user={is_new_user}, args={args}")
    
    user = await get_vpn_user(tg_id)
    can_set_referrer = user is None or user.referred_by_id is None
    
    logging.info(f"Referral check: user={user}, referred_by_id={user.referred_by_id if user else None}, can_set_referrer={can_set_referrer}, len(args)={len(args)}")
    
    if can_set_referrer and len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1].replace("ref_", "").upper()
        logging.info(f"Processing referral code: {ref_code} for user {tg_id}")
        referrer = await referrals.get_user_by_referral_code(ref_code)
        
        if referrer:
            logging.info(f"Found referrer: {referrer.tg_id} for code {ref_code}")
            if referrer.tg_id != tg_id:
                await referrals.set_referrer(tg_id, referrer.tg_id)
                logging.info(f"User {tg_id} registered via referral from {referrer.tg_id}")
            else:
                logging.warning(f"User {tg_id} tried to use their own referral code")
        else:
            logging.warning(f"Referral code {ref_code} not found for user {tg_id}")
    
    if len(args) > 1 and args[1].startswith("promo_"):
        promo_code = args[1].replace("promo_", "").upper()
        promo = await get_promo_code_by_code(promo_code)
        if not promo:
            sent_message = await message.answer(text=_("message_promo_not_found"), reply_markup=await get_main_menu_keyboard(user_id=tg_id))
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        if promo.expires_at and promo.expires_at < datetime.now():
            sent_message = await message.answer(text=_("message_promo_expired"), reply_markup=await get_main_menu_keyboard(user_id=tg_id))
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        if await has_activated_promo_code(tg_id, promo.id):
            sent_message = await message.answer(text=_("message_promo_already_activated"), reply_markup=await get_main_menu_keyboard(user_id=tg_id))
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
            return
    
        try:
            await activate_promo_code(tg_id, promo.id)
            sent_message = await message.answer(text=_("message_promo_activated").format(discount=promo.discount_percent), 
                             reply_markup=await get_main_menu_keyboard(user_id=tg_id))
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
        except Exception as e:
            logging.error(f"Failed to activate promo code {promo_code} for user {tg_id}: {e}", exc_info=True)
            sent_message = await message.answer(
                text=_("message_error") + "\n\n" + _("Failed to activate promo code. Please try again or contact support."),
                reply_markup=await get_main_menu_keyboard(user_id=tg_id)
            )
            await cleanup.register_message(tg_id, sent_message.message_id, MessageType.NAVIGATION)
    else:
        panel = get_panel()
        panel_profile = await panel.get_panel_user(tg_id)
        await _build_and_send_profile(cleanup, tg_id, panel_profile, user_name=message.from_user.first_name)

def register_commands(dp: Dispatcher):
    dp.include_router(router)
