import time

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from keyboards import get_user_profile_keyboard, get_help_keyboard
from db.methods import is_trial_available
from utils import marzban_api
import glv

router = Router(name="messages-router") 

@router.message(F.text == __("Access to VPN 🏄🏻‍♂️"))
async def profile(message: Message):
    marzban_profile = await marzban_api.get_marzban_profile(message.from_user.id)
    trial_available = await is_trial_available(message.from_user.id)
    message_text = get_profile_menu_string(marzban_profile)
    await message.answer(message_text, reply_markup=get_user_profile_keyboard(trial_available, glv.config['PANEL_GLOBAL'] + marzban_profile['subscription_url'] if marzban_profile else ""))
    
@router.message(F.text == __("Help 🕊"))
async def help(message: Message):
    await message.answer(text=_('What issue did you encounter?'), reply_markup=get_help_keyboard())

def register_messages(dp: Dispatcher):
    dp.include_router(router)

def get_profile_menu_string(marzban_profile):
    status = 'disabled'
    days_left = 0
    data_used = 0
    data_limit = 100
    if marzban_profile:
        status = marzban_profile['status']
        now = int(time.time())
        if marzban_profile['expire'] > now:
            days_left = (marzban_profile['expire'] - now) // 86400
        data_used = marzban_profile['used_traffic'] // 1073741824
        data_limit = marzban_profile['data_limit'] // 1073741824 if marzban_profile['data_limit'] else 0
    
    return f"Статус подписки: {status}\n\nОсталось дней: {days_left}\n\nТрафик: {data_used} GB / {data_limit} GB"
