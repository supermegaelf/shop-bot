from datetime import datetime

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
    trial_available = await is_trial_available(message.from_user.id)
    marzban_profile = await marzban_api.get_marzban_profile(message.from_user.id)
    if marzban_profile:
        url = glv.config['PANEL_GLOBAL'] + marzban_profile['subscription_url']
        status = _(marzban_profile['status'])
        expire_date = datetime.fromtimestamp(marzban_profile['expire']).strftime("%d.%m.%Y") if marzban_profile['expire'] else "∞"
        data_used = f"{marzban_profile['used_traffic'] / 1073741824:.2f}"
        data_limit = f"{marzban_profile['data_limit'] // 1073741824}" if marzban_profile['data_limit'] else "∞"
        subscription_limited = marzban_profile['status'] == "limited"
    else:
        url = ""
        status = "–"
        expire_date = "–"
        data_used = "–"
        data_limit = "–"
        subscription_limited = False
    
    subscription_limited = marzban_profile and marzban_profile['data_limit']
    await message.answer(text=_("subscription_data").format(status = status, expire_date = expire_date, data_used = data_used, data_limit = data_limit), 
                         reply_markup=get_user_profile_keyboard(trial_available, subscription_limited, url))
    
@router.message(F.text == __("Help 🕊"))
async def help(message: Message):
    await message.answer(text=_("Select the action ⬇️"), reply_markup=get_help_keyboard())

def register_messages(dp: Dispatcher):
    dp.include_router(router)
