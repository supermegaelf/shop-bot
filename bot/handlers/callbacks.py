from datetime import datetime, timedelta
import asyncio
import logging

from aiogram import Router, F, Dispatcher
from aiogram.types import CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from keyboards import (
    get_main_menu_keyboard,
    get_payment_keyboard,
    get_pay_keyboard,
    get_buy_menu_keyboard,
    get_xtr_pay_keyboard,
    get_back_to_help_keyboard,
    get_help_keyboard,
    get_months_keyboard,
    get_install_subscription_keyboard,
    get_user_profile_keyboard,
)
from db.methods import (
    is_trial_available,
    start_trial,
    get_vpn_user,
    get_user_promo_discount,
)
from utils import goods, yookassa, cryptomus, MessageCleanup, MessageType
from panel import get_panel
import glv

router = Router(name="callbacks-router")


def _format_profile_data(panel_profile):
    if panel_profile:
        url = panel_profile.subscription_url
        status = _(panel_profile.status)
        expire_date = (
            panel_profile.expire.strftime("%d.%m.%Y") if panel_profile.expire else "∞"
        )
        data_used = f"{panel_profile.used_traffic / 1073741824:.2f}"
        data_limit = (
            f"{panel_profile.data_limit // 1073741824}"
            if panel_profile.data_limit
            else "∞"
        )
        show_buy_traffic_button = (
            panel_profile.data_limit
            and (panel_profile.used_traffic / panel_profile.data_limit) > 0.9
        )
    else:
        url = ""
        status = "–"
        expire_date = "–"
        data_used = "–"
        data_limit = "–"
        show_buy_traffic_button = False
    
    return {
        "url": url,
        "status": status,
        "expire_date": expire_date,
        "data_used": data_used,
        "data_limit": data_limit,
        "show_buy_traffic_button": show_buy_traffic_button,
    }


async def _build_and_send_profile(cleanup: MessageCleanup, user_id: int, panel_profile):
    profile_data = _format_profile_data(panel_profile)
    
    keyboard = await get_user_profile_keyboard(
        user_id, profile_data["show_buy_traffic_button"], profile_data["url"]
    )
    
    await cleanup.send_profile(
        chat_id=user_id,
        text=_("subscription_data").format(
            status=profile_data["status"],
            expire_date=profile_data["expire_date"],
            data_used=profile_data["data_used"],
            data_limit=profile_data["data_limit"],
            link=glv.config["TG_INFO_CHANEL"],
        ),
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "vpn_access")
async def callback_vpn_access(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)

    await callback.answer()


@router.callback_query(F.data.startswith("months_"))
async def callback_month_amount_select(callback: CallbackQuery, state: FSMContext):

    months = int(callback.data.replace("months_", ""))
    keyboard = await get_buy_menu_keyboard(callback.from_user.id, months, "renew")

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.edit_navigation(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        text=_("message_traffic_renewal_info"),
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("extend_data_limit"))
async def callback_extend_data_limit(callback: CallbackQuery, state: FSMContext):

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    if not panel_profile or not panel_profile.data_limit or not panel_profile.expire:
        await callback.answer(_("message_error"), show_alert=True)
        return

    subscription_months_left = (
        panel_profile.expire.timestamp() - datetime.now().timestamp()
    ) / 2592000

    filtered_goods = [
        good
        for good in goods.get()
        if good["months"] > subscription_months_left and good["type"] == "update"
    ]
    if filtered_goods:
        min_good = min(filtered_goods, key=lambda good: good["months"])
        keyboard = await get_buy_menu_keyboard(
            callback.from_user.id, min_good["months"], "update"
        )

        cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
        await cleanup.edit_navigation(
            chat_id=callback.from_user.id,
            message_id=callback.message.message_id,
            text=_("message_select_traffic_amount"),
            reply_markup=keyboard,
        )
    else:
        await callback.answer(_("message_error"), show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "extend_data_limit_notification")
async def callback_extend_data_limit_notification(
    callback: CallbackQuery, state: FSMContext
):
    await state.update_data(payment_from_notification=True)

    await callback_extend_data_limit(callback)


@router.callback_query(F.data.startswith("pay_kassa_"))
async def callback_payment_kassa(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    data = callback.data.replace("pay_kassa_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return

    state_data = await state.get_data()
    from_notification = state_data.get("payment_from_notification", False) or (
        "profile_message_id" not in state_data
    )

    result = await yookassa.create_payment(
        callback.from_user.id, data, callback.from_user.language_code
    )

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    sent_message_id = await cleanup.send_payment(
        chat_id=callback.from_user.id,
        text=_("To be paid – {amount} ₽ ⬇️").format(amount=int(result["amount"])),
        reply_markup=get_pay_keyboard(result["url"], data),
    )

    from db.methods import add_payment, PaymentPlatform

    await add_payment(
        callback.from_user.id,
        data,
        callback.from_user.language_code,
        result["payment_id"],
        PaymentPlatform.YOOKASSA,
        message_id=sent_message_id,
        from_notification=from_notification,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pay_stars_"))
async def callback_payment_stars(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    data = callback.data.replace("pay_stars_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return

    state_data = await state.get_data()
    from_notification = state_data.get("payment_from_notification", False) or (
        "profile_message_id" not in state_data
    )

    good = goods.get(data)
    discount = await get_user_promo_discount(callback.from_user.id)
    price = int(good["price"]["stars"] * (1 - discount / 100))
    prices = [LabeledPrice(label="XTR", amount=price)]

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.cleanup_by_event(callback.from_user.id, "start_payment")

    sent_message = await glv.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=good["title"],
        currency="XTR",
        description=_("To be paid – {amount} ⭐️ ⬇️").format(amount=int(price)),
        prices=prices,
        provider_token="",
        payload=data,
        reply_markup=get_xtr_pay_keyboard(data),
    )

    await cleanup.register_message(
        callback.from_user.id, sent_message.message_id, MessageType.PAYMENT
    )

    from db.methods import add_payment, PaymentPlatform

    await add_payment(
        callback.from_user.id,
        data,
        callback.from_user.language_code,
        data,
        PaymentPlatform.TELEGRAM,
        message_id=sent_message.message_id,
        from_notification=from_notification,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pay_crypto_"))
async def callback_payment_crypto(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    data = callback.data.replace("pay_crypto_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return

    state_data = await state.get_data()
    from_notification = state_data.get("payment_from_notification", False) or (
        "profile_message_id" not in state_data
    )

    result = await cryptomus.create_payment(
        callback.from_user.id, data, callback.from_user.language_code
    )
    now = datetime.now()
    expire_date = (now + timedelta(minutes=60)).strftime("%d/%m/%Y, %H:%M")

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    sent_message_id = await cleanup.send_payment(
        chat_id=callback.from_user.id,
        text=_("To be paid – {amount} $ ⬇️").format(
            amount=result["amount"], date=expire_date
        ),
        reply_markup=get_pay_keyboard(result["url"], data),
    )

    from db.methods import add_payment, PaymentPlatform

    await add_payment(
        callback.from_user.id,
        data,
        callback.from_user.language_code,
        result["order_id"],
        PaymentPlatform.CRYPTOMUS,
        message_id=sent_message_id,
        from_notification=from_notification,
    )

    await callback.answer()


@router.callback_query(F.data == ("trial"))
async def callback_trial(callback: CallbackQuery, state: FSMContext):

    result = await is_trial_available(callback.from_user.id)
    if not result:
        await callback.answer(_("message_subscription_access"), show_alert=True)
        return
    result = await get_vpn_user(callback.from_user.id)
    panel = get_panel()
    panel_profile = await panel.generate_test_subscription(result.vpn_id)
    if not panel_profile:
        await callback.answer(_("message_error"), reply_markup=get_main_menu_keyboard())
        logging.error(
            "Failed to generate test subscription for user %s", callback.from_user.id
        )
        return
    else:
        logging.info("Test subscription generated for user %s", callback.from_user.id)

    await start_trial(callback.from_user.id)
    subscription_url = panel_profile.subscription_url

    await callback.message.delete()

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_important(
        chat_id=callback.from_user.id,
        text=_("message_new_subscription_created"),
        reply_markup=get_install_subscription_keyboard(
            subscription_url, callback.from_user.language_code
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "payment")
async def callback_payment(callback: CallbackQuery, state: FSMContext):

    keyboard = await get_months_keyboard(callback.from_user.id)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.edit_navigation(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        text=_("message_select_payment_period"),
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(F.data == "faq")
async def callback_frequent_questions(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    from_profile = "profile_message_id" in data

    await callback.message.delete()

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_frequent_questions").format(shop_name=glv.config["SHOP_NAME"]),
        reply_markup=get_back_to_help_keyboard(from_profile=from_profile),
    )
    await callback.answer()


@router.callback_query(F.data == "help_from_profile")
async def callback_help_from_profile(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception:
        pass

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_select_action"),
        reply_markup=get_help_keyboard(from_profile=True),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_select_action"),
        reply_markup=get_help_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data in goods.get_callbacks())
async def callback_payment_method_select(callback: CallbackQuery, state: FSMContext):

    good = goods.get(callback.data)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.edit_navigation(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        text=_("message_select_payment_method"),
        reply_markup=get_payment_keyboard(good),
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_profile")
async def callback_back_to_profile(callback: CallbackQuery, state: FSMContext):
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.back_to_profile(callback.from_user.id, callback.message.message_id)

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)
    
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_payment_"))
async def callback_back_to_payment(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    good_callback = callback.data.replace("back_to_payment_", "")
    good = goods.get(good_callback)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.send_navigation(
        chat_id=callback.from_user.id,
        text=_("message_select_payment_method"),
        reply_markup=get_payment_keyboard(good),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_traffic_"))
async def callback_back_to_traffic(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    parts = callback.data.replace("back_to_traffic_", "").split("_")
    purchase_type = parts[0]
    months = int(parts[1])

    keyboard = await get_buy_menu_keyboard(callback.from_user.id, months, purchase_type)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    if purchase_type == "renew":
        await cleanup.send_navigation(
            chat_id=callback.from_user.id,
            text=_("message_traffic_renewal_info"),
            reply_markup=keyboard,
        )
    else:
        await cleanup.send_navigation(
            chat_id=callback.from_user.id,
            text=_("message_select_traffic_amount"),
            reply_markup=keyboard,
        )

    await callback.answer()


@router.callback_query(F.data == "dismiss_notification")
async def callback_dismiss_notification(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)

    try:
        await cleanup.cleanup_by_event(callback.from_user.id, "back_to_profile")
    except Exception:
        pass

    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)


@router.callback_query(F.data == "dismiss_payment_success")
async def callback_dismiss_payment_success(callback: CallbackQuery, state: FSMContext):
    logging.info(f"dismiss_payment_success called by user {callback.from_user.id}")

    try:
        await callback.message.delete()
        logging.info(f"Message {callback.message.message_id} deleted")
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")

    await callback.answer()

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)

    try:
        await cleanup.cleanup_by_event(callback.from_user.id, "back_to_profile")
    except Exception as e:
        logging.warning(f"Cleanup failed: {e}")

    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)

    logging.info(f"Profile sent to user {callback.from_user.id}")


@router.callback_query(F.data == "dismiss_payment_success_notification")
async def callback_dismiss_payment_success_notification(
    callback: CallbackQuery, state: FSMContext
):
    logging.info(
        f"dismiss_payment_success_notification called by user {callback.from_user.id}"
    )

    try:
        await callback.message.delete()
        logging.info(f"Message {callback.message.message_id} deleted")
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")

    await callback.answer()

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)

    try:
        await cleanup.cleanup_by_event(callback.from_user.id, "back_to_profile")
    except Exception as e:
        logging.warning(f"Cleanup failed: {e}")

    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)

    logging.info(f"Profile sent to user {callback.from_user.id}")


@router.callback_query(F.data == "dismiss_after_install")
async def callback_dismiss_after_install(callback: CallbackQuery, state: FSMContext):
    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)
    await cleanup.back_to_profile(callback.from_user.id, callback.message.message_id)

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)

    await _build_and_send_profile(cleanup, callback.from_user.id, panel_profile)

    await callback.answer()


def register_callbacks(dp: Dispatcher):
    dp.include_router(router)
