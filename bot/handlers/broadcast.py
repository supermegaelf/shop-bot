import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _

from filters import IsAdminFilter
from db.methods import get_vpn_users
from keyboards import get_confirmation_keyboard, get_main_menu_keyboard, get_broadcast_confirmation_keyboard
from utils import MessageCleanup, try_delete_message
import glv

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

router = Router(name="broadcast-router")

@router.message(IsAdminFilter(is_admin=True), Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=_("message_broadcast_start"),
        reply_markup=None,
    )
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message, IsAdminFilter(is_admin=True))
async def process_message(message: Message, state: FSMContext):
    await try_delete_message(message)
    
    broadcast_message = message.text or message.caption or ""
    if not broadcast_message:
        return
    
    await state.update_data(broadcast_message=broadcast_message)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=_("message_confirm_broadcast").format(text=broadcast_message),
        reply_markup=get_broadcast_confirmation_keyboard(),
    )
    await state.set_state(BroadcastStates.waiting_for_confirmation)

def register_broadcast(dp: Dispatcher):
    dp.include_router(router)
