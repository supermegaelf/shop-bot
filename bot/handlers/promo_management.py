from datetime import datetime
import logging

from aiogram import Router, F, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _

from filters import IsAdminCallbackFilter
from db.methods import (
    get_active_promo_codes,
    add_promo_code,
    delete_promo_code,
    get_promo_code_by_id
)
from keyboards import (
    get_promo_codes_management_keyboard,
    get_promo_delete_keyboard,
    get_promo_back_keyboard,
    get_admin_management_keyboard
)
from utils import MessageCleanup
import glv

router = Router(name="promo-management-router")


class PromoManagementStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_discount = State()
    waiting_for_expires_at = State()


@router.callback_query(F.data == "admin_promo_codes", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_promo_codes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await state.clear()
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_promo_management"),
        reply_markup=get_promo_codes_management_keyboard(),
        reuse_message=callback.message,
    )


@router.callback_query(F.data == "admin_add_promo", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_add_promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_enter_promo_code"),
        reply_markup=get_promo_back_keyboard(),
        reuse_message=callback.message,
    )
    
    await state.set_state(PromoManagementStates.waiting_for_code)


@router.message(PromoManagementStates.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    if message.from_user.id not in glv.config['ADMINS']:
        return
    
    await try_delete_message(message)
    
    code = message.text.strip().upper()
    if not code:
        cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
        await cleanup.send_navigation(
            chat_id=message.from_user.id,
            text=_("message_invalid_promo_code"),
            reply_markup=get_promo_back_keyboard(),
        )
        return
    
    await state.update_data(promo_code=code)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=_("message_enter_promo_discount"),
        reply_markup=get_promo_back_keyboard(),
    )
    
    await state.set_state(PromoManagementStates.waiting_for_discount)


@router.message(PromoManagementStates.waiting_for_discount)
async def process_promo_discount(message: Message, state: FSMContext):
    if message.from_user.id not in glv.config['ADMINS']:
        return
    
    await try_delete_message(message)
    
    try:
        discount = int(message.text.strip())
        if discount < 1 or discount > 100:
            raise ValueError
    except ValueError:
        cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
        await cleanup.send_navigation(
            chat_id=message.from_user.id,
            text=_("message_invalid_discount"),
            reply_markup=get_promo_back_keyboard(),
        )
        return
    
    await state.update_data(discount=discount)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=_("message_enter_promo_expires_at"),
        reply_markup=get_promo_back_keyboard(),
    )
    
    await state.set_state(PromoManagementStates.waiting_for_expires_at)


@router.message(PromoManagementStates.waiting_for_expires_at)
async def process_promo_expires_at(message: Message, state: FSMContext):
    if message.from_user.id not in glv.config['ADMINS']:
        return
    
    await try_delete_message(message)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    
    data = await state.get_data()
    code = data.get("promo_code")
    discount = data.get("discount")
    
    try:
        expires_at = datetime.strptime(message.text.strip(), "%d.%m.%Y")
    except ValueError:
        await cleanup.send_navigation(
            chat_id=message.from_user.id,
            text=_("message_invalid_date_format"),
            reply_markup=get_promo_back_keyboard(),
        )
        return
    
    try:
        await add_promo_code(code, discount, expires_at)
        
        await cleanup.send_navigation(
            chat_id=message.from_user.id,
            text=_("message_promo_added").format(code=code, discount=discount),
            reply_markup=get_promo_codes_management_keyboard(),
        )
    except Exception as e:
        logging.error(f"Failed to add promo code: {e}", exc_info=True)
        error_text = _("message_error")
        if "Duplicate entry" in str(e) or "UNIQUE constraint" in str(e):
            error_text = _("message_promo_already_exists")
        await cleanup.send_navigation(
            chat_id=message.from_user.id,
            text=error_text,
            reply_markup=get_promo_codes_management_keyboard(),
        )
    
    await state.clear()


@router.callback_query(F.data == "admin_delete_promo", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_delete_promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    promo_codes = await get_active_promo_codes()
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    if not promo_codes:
        await cleanup.send_navigation(
            chat_id=callback.from_user.id,
            text=_("message_no_active_promos"),
            reply_markup=get_promo_back_keyboard(),
            reuse_message=callback.message,
        )
        return
    
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_select_promo_to_delete"),
        reply_markup=get_promo_delete_keyboard(promo_codes),
        reuse_message=callback.message,
    )


@router.callback_query(F.data.startswith("delete_promo_"), IsAdminCallbackFilter(is_admin=True))
async def callback_delete_promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    promo_id = int(callback.data.replace("delete_promo_", ""))
    
    try:
        promo = await get_promo_code_by_id(promo_id)
        if not promo:
            from bot.utils.telegram_message import safe_edit_or_send
            await safe_edit_or_send(
                callback.message,
                text=_("message_error"),
                debug=glv.MESSAGE_CLEANUP_DEBUG,
            )
            return
        
        await delete_promo_code(promo_id)
        
        cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
        await cleanup.send_navigation(
            chat_id=callback.from_user.id,
            text=_("message_promo_deleted").format(code=promo.code),
            reply_markup=get_promo_codes_management_keyboard(),
            reuse_message=callback.message,
        )
    except Exception as e:
        logging.error(f"Failed to delete promo code: {e}", exc_info=True)
        from bot.utils.telegram_message import safe_edit_or_send
        await safe_edit_or_send(
            callback.message,
            text=_("message_error"),
            debug=glv.MESSAGE_CLEANUP_DEBUG,
        )


@router.callback_query(F.data == "admin_active_promos", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_active_promos(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    promo_codes = await get_active_promo_codes()
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    if not promo_codes:
        await cleanup.send_navigation(
            chat_id=callback.from_user.id,
            text=_("message_no_active_promos"),
            reply_markup=get_promo_back_keyboard(),
            reuse_message=callback.message,
        )
        return
    
    text_parts = []
    for i, promo in enumerate(promo_codes, 1):
        expires_text = promo.expires_at.strftime("%d.%m.%Y")
        text_parts.append(
            f"{i}. {_('message_promo_info').format(code=promo.code, discount=promo.discount_percent, expires_at=expires_text)}"
        )
    
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text="\n\n".join(text_parts),
        reply_markup=get_promo_back_keyboard(),
        reuse_message=callback.message,
    )


def register_promo_management(dp: Dispatcher):
    dp.include_router(router)

