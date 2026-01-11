import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import get_admin_referral_keyboard, get_admin_referral_stats_keyboard, get_admin_referral_list_keyboard, get_admin_referral_user_keyboard, get_admin_referral_search_keyboard
from filters import IsAdminCallbackFilter
from utils import MessageCleanup, safe_answer, get_i18n_string, referrals
from db.methods import get_vpn_user
import glv

router = Router(name="admin-referrals-router")

class AdminReferralSearchStates(StatesGroup):
    waiting_for_user_id = State()

@router.callback_query(F.data == "admin_referrals", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_referrals(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)
    
    lang = callback.from_user.language_code or 'ru'
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=get_i18n_string("message_admin_management", lang),
        reply_markup=get_admin_referral_keyboard(lang),
        reuse_message=callback.message
    )

@router.callback_query(F.data == "admin_referral_stats", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_referral_stats(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)
    
    lang = callback.from_user.language_code or 'ru'
    
    stats = await referrals.get_admin_referral_stats()
    
    text = get_i18n_string("admin_referral_stats", lang).format(
        referrals_count=stats['referrals_count'],
        conversion=stats['conversion'],
        purchased=stats['purchased'],
        total=stats['total'],
        total_bonus=stats['total_bonus']
    )
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=get_admin_referral_stats_keyboard(lang),
        reuse_message=callback.message
    )

@router.callback_query(F.data == "admin_referral_list", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_referral_list(callback: CallbackQuery, state: FSMContext):
    await callback_admin_referral_list_page(callback, state, page=1)

@router.callback_query(F.data.startswith("admin_referral_page_"), IsAdminCallbackFilter(is_admin=True))
async def callback_admin_referral_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])
    await callback_admin_referral_list_page(callback, state, page)

async def callback_admin_referral_list_page(callback: CallbackQuery, state: FSMContext, page: int):
    await safe_answer(callback)
    
    lang = callback.from_user.language_code or 'ru'
    
    data = await referrals.get_referrers_list(page=page, per_page=5)
    
    has_referrers = bool(data['referrers'])
    
    if not has_referrers:
        text = get_i18n_string("admin_referral_no_referrals", lang)
    else:
        text = ""
        for i, ref in enumerate(data['referrers'], start=1):
            try:
                chat = await glv.bot.get_chat(ref['referrer_id'])
                username = f"@{chat.username}" if chat.username else (chat.first_name or f"ID: {ref['referrer_id']}")
            except:
                username = f"ID: {ref['referrer_id']}"
            
            index = (page - 1) * 5 + i
            text += get_i18n_string("admin_referral_list_item", lang).format(
                index=index,
                username=username,
                count=ref['referrals_count'],
                days=ref['earned_days']
            ) + "\n\n"
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=get_admin_referral_list_keyboard(page, data['total_pages'], lang, has_referrers),
        reuse_message=callback.message
    )

@router.callback_query(F.data == "admin_referral_search", IsAdminCallbackFilter(is_admin=True))
async def callback_admin_referral_search(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)
    
    lang = callback.from_user.language_code or 'ru'
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=get_i18n_string("admin_referral_search_prompt", lang),
        reply_markup=get_admin_referral_search_keyboard(lang),
        reuse_message=callback.message
    )
    
    await state.set_state(AdminReferralSearchStates.waiting_for_user_id)

@router.message(AdminReferralSearchStates.waiting_for_user_id)
async def process_referral_search(message, state: FSMContext):
    admins = glv.config.get('ADMINS', [])
    if message.from_user.id not in admins:
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(get_i18n_string("message_error", message.from_user.language_code or 'ru'))
        await state.clear()
        return
    
    lang = message.from_user.language_code or 'ru'
    
    user = await get_vpn_user(user_id)
    if not user:
        await message.answer(get_i18n_string("admin_referral_user_not_found", lang))
        await state.clear()
        return
    
    stats = await referrals.get_referral_stats(user_id)
    data = await referrals.get_user_referrals(user_id, page=1, per_page=5)
    
    try:
        chat = await glv.bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else (chat.first_name or f"ID: {user_id}")
    except:
        username = f"ID: {user_id}"
    
    text = get_i18n_string("admin_referral_user_info", lang).format(
        username=username,
        user_id=user_id,
        invited_count=stats['invited_count'],
        earned_days=stats['earned_days']
    ) + "\n\n"
    
    for i, ref in enumerate(data['referrals'], start=1):
        try:
            ref_chat = await glv.bot.get_chat(ref['referee_id'])
            ref_username = f"@{ref_chat.username}" if ref_chat.username else (ref_chat.first_name or f"ID: {ref['referee_id']}")
        except:
            ref_username = f"ID: {ref['referee_id']}"
        
        text += get_i18n_string("admin_referral_referee_item", lang).format(
            index=i,
            username=ref_username,
            user_id=ref['referee_id'],
            date="—",
            purchases=ref['purchases'],
            days=ref['earned_days']
        ) + "\n\n"
    
    if not data['referrals']:
        text += get_i18n_string("admin_referral_no_referrals", lang)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=message.from_user.id,
        text=text,
        reply_markup=get_admin_referral_user_keyboard(user_id, data['page'], data['total_pages'], lang)
    )
    
    await state.clear()

def register_admin_referrals(dp):
    from aiogram import Dispatcher
    dp.include_router(router)
