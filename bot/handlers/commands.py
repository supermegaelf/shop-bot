import asyncio

from aiogram import Router
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.chat_action import ChatActionSender

from keyboards import get_main_menu_keyboard

router = Router(name="commands-router") 

@router.message(
    Command("start")
)
async def start(message: Message):
    await message.answer(_("message_welcome").format(name=message.from_user.first_name))
    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
            await asyncio.sleep(1)
    await message.answer(_("message_select_action"), reply_markup=get_main_menu_keyboard())

def register_commands(dp: Dispatcher):
    dp.include_router(router)
