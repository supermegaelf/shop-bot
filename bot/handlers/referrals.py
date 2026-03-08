import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import get_referral_menu_keyboard
from utils import MessageCleanup, try_delete_message, safe_answer, referrals, get_i18n_string
from db.methods import get_vpn_user
import glv

router = Router(name="referrals-router")

class ReferralSearchStates(StatesGroup):
    waiting_for_user_id = State()

@router.callback_query(F.data == "referral_menu")
async def callback_referral_menu(callback: CallbackQuery, state: FSMContext):
    await safe_answer(callback)
    
    tg_id = callback.from_user.id
    lang = callback.from_user.language_code or 'ru'
    
    stats = await referrals.get_referral_stats(tg_id)
    
    code = await referrals.ensure_referral_code(tg_id)
    bot_info = await glv.bot.get_me()
    bot_username = bot_info.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{code}"
    
    text = f"{get_i18n_string('referral_stats_title', lang)}\n\n"
    text += f"{get_i18n_string('referral_invited_count', lang).format(count=stats['invited_count'])}\n"
    text += f"{get_i18n_string('referral_earned_days', lang).format(days=stats['earned_days'])}\n\n"
    text += f"{get_i18n_string('referral_how_title', lang)}\n\n"
    text += get_i18n_string('referral_how_it_works', lang)
    
    keyboard = get_referral_menu_keyboard(lang, referral_link)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=tg_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        reuse_message=callback.message
    )

@router.inline_query()
async def referral_inline_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    lang = inline_query.from_user.language_code or 'ru'
    
    code = await referrals.ensure_referral_code(user_id)
    if not code:
        await inline_query.answer([], cache_time=1)
        return
    
    bot_info = await inline_query.bot.get_me()
    bot_username = bot_info.username
    
    referral_link = f"https://t.me/{bot_username}?start=ref_{code}"
    
    message_text = get_i18n_string("referral_inline_message", lang).format(referral_link=referral_link)
    
    result = InlineQueryResultArticle(
        id="referral",
        title=get_i18n_string("referral_share_button", lang),
        description=get_i18n_string("referral_menu_title", lang),
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            disable_web_page_preview=True
        )
    )
    
    await inline_query.answer([result], cache_time=1)

def register_referrals(dp):
    from aiogram import Dispatcher
    dp.include_router(router)
