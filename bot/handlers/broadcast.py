import asyncio
from typing import Union

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, PhotoSize, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _

from filters import IsAdminFilter
from db.methods import get_vpn_users
from keyboards import get_confirmation_keyboard, get_main_menu_keyboard

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

router = Router(name="broadcast-router")

@router.message(IsAdminFilter(is_admin=True), Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    await message.answer(_("message_broadcast_start"))
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message)
async def process_message(message: Message, state: FSMContext):
    if message.photo:
        message_data = {
            'text': message.caption or "",
            'has_photo': True,
            'photo_file_id': message.photo[-1].file_id,
            'message_type': 'photo'
        }
        preview_text = f"[📷 Изображение]\n{message_data['text']}" if message_data['text'] else "[📷 Изображение]"
    else:
        message_data = message.text
        preview_text = message.text
    
    await state.update_data(broadcast_message=message_data)
    
    await message.answer(
        _("message_confirm_broadcast").format(text=preview_text), 
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_confirmation)

@router.message(BroadcastStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text not in [_("button_yes"), _("button_no")]:
        await message.answer(_("message_invalid_confirmation"))
        return

    if message.text == _("button_no"):
        await message.answer(_("mesage_broadcast_cancelled"))
        await state.clear()
        return

    data = await state.get_data()
    broadcast_data = data['broadcast_message']
    
    await message.answer(_("message_broadcast_started"), reply_markup=get_main_menu_keyboard(lang=message.from_user.language_code))
    
    success_count = 0
    fail_count = 0

    users = await get_vpn_users()
    
    for user in users:
        try:
            if isinstance(broadcast_data, dict) and broadcast_data.get('message_type') == 'photo':
                await bot.send_photo(
                    chat_id=user.tg_id,
                    photo=broadcast_data['photo_file_id'],
                    caption=broadcast_data['text'],
                    disable_web_page_preview=True
                )
            else:
                text = broadcast_data if isinstance(broadcast_data, str) else broadcast_data.get('text', '')
                await bot.send_message(
                    chat_id=user.tg_id, 
                    text=text,
                    disable_web_page_preview=True
                )
            success_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            fail_count += 1
    
    await message.answer(_("message_broadcast_completed").format(success_count=success_count, fail_count=fail_count))
    await state.clear()

def register_broadcast(dp: Dispatcher):
    dp.include_router(router)