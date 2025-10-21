import asyncio
from datetime import datetime

from aiogram import Router
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.chat_action import ChatActionSender

from keyboards import get_main_menu_keyboard
from .messages import profile, help
from db.methods import get_promo_code_by_code, has_activated_promo_code, activate_promo_code

router = Router(name="commands-router")

@router.message(
    Command("start")
)
async def start(message: Message):
    args = message.text.split()
    tg_id = message.from_user.id
    
    if len(args) > 1 and args[1].startswith("promo_"):
        promo_code = args[1].replace("promo_", "").upper()
        promo = await get_promo_code_by_code(promo_code)
        if not promo:
            await message.answer(text=_("message_promo_not_found"), reply_markup=get_main_menu_keyboard())
    
        if promo.expires_at and promo.expires_at < datetime.now():
            await message.answer(text=_("message_promo_expired"), reply_markup=get_main_menu_keyboard())
    
        if await has_activated_promo_code(tg_id, promo.id):
            await message.answer(text=_("message_promo_already_activated"), reply_markup=get_main_menu_keyboard())
    
        await activate_promo_code(tg_id, promo.id)
        await message.answer(text=_("message_promo_activated").format(discount=promo.discount_percent), 
                         reply_markup=get_main_menu_keyboard())   
    else:
        await message.answer(_("message_welcome").format(name=message.from_user.first_name), reply_markup=get_main_menu_keyboard())

def register_commands(dp: Dispatcher):
    dp.include_router(router)
