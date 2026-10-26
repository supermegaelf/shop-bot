from datetime import datetime

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards import get_help_keyboard
from db.methods import get_promo_code_by_code, has_activated_promo_code, activate_promo_code
from panel import get_panel

import glv
from utils import MessageCleanup, try_delete_message, safe_answer

router = Router(name="messages-router")


async def _build_and_send_profile(cleanup, user_id: int, panel_profile, user_name: str = None):
    from keyboards import get_main_menu_keyboard
    
    if user_name is None:
        try:
            chat = await glv.bot.get_chat(user_id)
            user_name = chat.first_name or chat.username or "пользователь"
        except Exception:
            user_name = "пользователь"
    
    has_subscription = panel_profile is not None and panel_profile.subscription_url and panel_profile.subscription_url.strip() != ""
    keyboard = await get_main_menu_keyboard(user_id=user_id, has_subscription=has_subscription)
    
    await cleanup.send_profile(
        chat_id=user_id,
        text=_("main_menu_news").format(
            name=user_name,
            link=glv.config['TG_INFO_CHANEL']
        ),
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


class PromoStates(StatesGroup):
    waiting_for_promo = State()

@router.message(F.text == __("button_vpn_access"))
async def profile(message: Message, state: FSMContext):
    panel = get_panel()
    panel_profile = await panel.get_panel_user(message.from_user.id)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await _build_and_send_profile(cleanup, message.from_user.id, panel_profile, user_name=message.from_user.first_name)

@router.message(F.text == __("button_help"))
async def help(message: Message, state: FSMContext):
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=_("message_select_action"),
        reply_markup=get_help_keyboard()
    )

@router.callback_query(lambda c: c.data == "enter_promo")
async def promo_start(callback: CallbackQuery, state: FSMContext):
    kb = [[InlineKeyboardButton(text=_("button_back"), callback_data="back_to_profile")]]
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_enter_promo"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        reuse_message=callback.message,
    )
    
    await state.set_state(PromoStates.waiting_for_promo)
    await safe_answer(callback)

@router.message(PromoStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    promo_code = message.text.strip().upper()
    tg_id = message.from_user.id

    await try_delete_message(message)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    
    promo = await get_promo_code_by_code(promo_code)
    kb = [[InlineKeyboardButton(text=_("button_back"), callback_data="back_to_profile")]]
    
    if not promo:
        await cleanup.send_navigation(
            chat_id=tg_id,
            text=_("message_promo_not_found"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.clear()
        return

    if promo.expires_at and promo.expires_at < datetime.now():
        await cleanup.send_navigation(
            chat_id=tg_id,
            text=_("message_promo_expired"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.clear()
        return

    if await has_activated_promo_code(tg_id, promo.id):
        await cleanup.send_navigation(
            chat_id=tg_id,
            text=_("message_promo_already_activated"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.clear()
        return

    await activate_promo_code(tg_id, promo.id)
    await cleanup.send_navigation(
        chat_id=tg_id,
        text=_("message_promo_activated").format(discount=promo.discount_percent),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.clear()

def register_messages(dp: Dispatcher):
    dp.include_router(router)
