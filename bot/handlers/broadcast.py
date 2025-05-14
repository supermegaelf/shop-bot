import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _

from filters import IsAdminFilter
from db.methods import get_vpn_users
from keyboards import get_confirmation_keyboard

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

router = Router(name="broadcast-router")

@router.message(Command("broadcast"), IsAdminFilter(is_admin=True))
async def start_broadcast(message: Message, state: FSMContext):
    await message.answer("message_broadcast_start")
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message)
async def process_message(message: Message, state: FSMContext):
    await state.update_data(broadcast_message=message.text)
    await message.answer(_("message_confirm_broadcast").format(message.text), reply_markup=get_confirmation_keyboard())
    await state.set_state(BroadcastStates.waiting_for_confirmation)

@router.message(BroadcastStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text.lower() not in [_("button_yes"), _("button_no")]:
        await message.answer("message_invalid_confirmation")
        return

    if message.text.lower() == _("button_no"):
        await message.answer("mesage_broadcast_cancelled")
        await state.clear()
        return

    data = await state.get_data()
    broadcast_message = data['broadcast_message']
    
    await message.answer("message_broadcast_started")
    
    success_count = 0
    fail_count = 0

    users = await get_vpn_users()
    
    for user in users:
        try:
            await bot.send_message(user.tg_id, broadcast_message)
            success_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            fail_count += 1
    
    await message.answer(_("message_broadcast_completed").format(success_count=success_count, fail_count=fail_count))
    await state.clear()

def register_broadcast(dp: Dispatcher):
    dp.include_router(router)