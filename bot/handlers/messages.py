import time

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from .commands import start
from keyboards import get_buy_menu_keyboard, get_back_keyboard, get_main_menu_keyboard, get_user_profile_keyboard
from db.methods import is_trial_available, disable_trial_availability, get_marzban_profile_db
from utils import marzban_api
import glv

router = Router(name="messages-router") 

@router.message(F.text == __("Join 🏄🏻‍♂️"))
async def profile(message: Message):
    marzban_profile = await marzban_api.get_marzban_profile(message.from_user.id)
    trial_available = is_trial_available(message.from_user.id)
    subscription_description = "Статус подписки: {status}\n\nОсталось дней: {days_left}\n\nТрафик: {data_used} GB/{data_limit} GB"
    await message.answer(subscription_description.format(
        status = marzban_profile['status'], 
        days_left = (int(time.time()) - marzban_profile['expire'])//86400,
        data_used = 0 if marzban_profile is None or marzban_profile['used_traffic'] == 0 else marzban_profile['used_traffic']//1073741824,
        data_limit = 0 if marzban_profile is None or marzban_profile['data_limit'] == 0 else marzban_profile['data_limit']//1073741824
        ), reply_markup=get_user_profile_keyboard(trial_available, glv.config['PANEL_GLOBAL'] + marzban_profile['subscription_url']))

@router.message(F.text == __("Frequent questions ℹ️"))
async def information(message: Message):
    await message.answer(
        _("Follow the <a href=\"{link}\">link</a> 🔗").format(
            link=glv.config['ABOUT']),
        reply_markup=get_back_keyboard())

@router.message(F.text == __("Support ❤️"))
async def support(message: Message):
    await message.answer(
        _("Follow the <a href=\"{link}\">link</a> and ask us a question. We are always happy to help 🤗").format(
            link=glv.config['SUPPORT_LINK']),
        reply_markup=get_back_keyboard())

@router.message(F.text == __("⏪ Back"))
async def start_text(message: Message):
    await start(message)

def register_messages(dp: Dispatcher):
    dp.include_router(router)
