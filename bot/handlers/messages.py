from datetime import datetime

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import get_user_profile_keyboard, get_help_keyboard, get_main_menu_keyboard
from db.methods import get_promo_code_by_code, has_activated_promo_code, activate_promo_code
from panel import get_panel

import glv

router = Router(name="messages-router") 

class PromoStates(StatesGroup):
    waiting_for_promo = State()

@router.message(F.text == __("button_vpn_access"))
async def profile(message: Message):
    panel = get_panel()
    panel_profile = await panel.get_panel_user(message.from_user.id)
    if panel_profile:
        url = panel_profile.subscription_url
        status = _(panel_profile.status)
        expire_date = panel_profile.expire.strftime("%d.%m.%Y") if panel_profile.expire else "∞"
        data_used = f"{panel_profile.used_traffic / 1073741824:.2f}"
        data_limit = f"{panel_profile.data_limit // 1073741824}" if panel_profile.data_limit else "∞"
        show_buy_traffic_button = panel_profile.data_limit and (panel_profile.used_traffic / panel_profile.data_limit) > 0.9
    else:
        url = ""
        status = "–"
        expire_date = "–"
        data_used = "–"
        data_limit = "–"
        show_buy_traffic_button = False
    keyboard = await get_user_profile_keyboard(message.from_user.id, show_buy_traffic_button, url)
    await message.answer(text=_("subscription_data").format(status = status, expire_date = expire_date, data_used = data_used, data_limit = data_limit, link = glv.config['TG_INFO_CHANEL']), 
                            reply_markup = keyboard,
                            disable_web_page_preview = True)
    
@router.message(F.text == __("button_help"))
async def help(message: Message):
    await message.answer(text=_("message_select_action"), reply_markup=get_help_keyboard())

@router.callback_query(lambda c: c.data == "enter_promo")
async def promo_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=_("message_enter_promo"))
    await state.set_state(PromoStates.waiting_for_promo)
    await callback.answer()

@router.message(PromoStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    promo_code = message.text.strip().upper()
    tg_id = message.from_user.id

    promo = await get_promo_code_by_code(promo_code)
    if not promo:
        await message.answer(text=_("message_promo_not_found"))
        await state.clear()
        return
    
    if promo.expires_at and promo.expires_at < datetime.now():
        await message.answer(text=_("message_promo_expired"))
        await state.clear()
        return
    
    if await has_activated_promo_code(tg_id, promo.id):
        await message.answer(text=_("message_promo_already_activated"))
        await state.clear()
        return
    
    await activate_promo_code(tg_id, promo.id)
    await message.answer(text=_("message_promo_activated").format(discount=promo.discount_percent), 
                         reply_markup=get_main_menu_keyboard())
    await state.clear()

def register_messages(dp: Dispatcher):
    dp.include_router(router)
