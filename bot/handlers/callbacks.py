from datetime import datetime, timedelta
import asyncio
import logging

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import CallbackQuery, LabeledPrice
from aiogram.utils.i18n import gettext as _
from panel.panel_provider import get_panel

from keyboards import get_main_menu_keyboard, get_payment_keyboard, get_pay_keyboard, \
    get_buy_menu_keyboard, get_xtr_pay_keyboard, get_back_to_help_keyboard, get_help_keyboard, \
    get_months_keyboard, get_support_keyboard, get_install_subscription_keyboard
from db.methods import is_trial_available, start_trial, get_vpn_user, get_user_promo_discount

from utils import goods, yookassa, cryptomus
from panel import get_panel
import glv

router = Router(name="callbacks-router")

@router.callback_query(F.data == "vpn_access")
async def callback_vpn_access(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    if panel_profile:
        url = panel_profile.subscription_url
        status = _(panel_profile.status)
        expire_date = panel_profile.expire.strftime("%d.%m.%Y") if panel_profile.expire else "∞"
        data_used = f"{panel_profile.used_traffic / 1073741824:.2f}"
        data_limit = f"{panel_profile.data_limit // 1073741824}" if panel_profile.data_limit else "∞"
        show_buy_traffic_button = panel_profile.data_limit and (panel_profile.used_traffic / panel_profile.data_limit) > 0.9
    else:
        url = ""
        status = "–"
        expire_date = "–"
        data_used = "–"
        data_limit = "–"
        show_buy_traffic_button = False

    from keyboards import get_user_profile_keyboard
    keyboard = await get_user_profile_keyboard(callback.from_user.id, show_buy_traffic_button, url)
    await callback.message.answer(
        text=_("subscription_data").format(
            status=status,
            expire_date=expire_date,
            data_used=data_used,
            data_limit=data_limit,
            link=glv.config['TG_INFO_CHANEL']
        ),
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data.startswith("months_"))
async def callback_month_amount_select(callback: CallbackQuery):
    await callback.message.delete()
    months = int(callback.data.replace("months_", ""))
    keyboard = await get_buy_menu_keyboard(callback.from_user.id, months, "renew")
    await callback.message.answer(text=_("message_traffic_renewal_info"), reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("extend_data_limit"))
async def callback_extend_data_limit(callback: CallbackQuery):
    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    if not panel_profile or not panel_profile.data_limit or not panel_profile.expire:
        await callback.answer(_("message_error"), reply_markup=get_main_menu_keyboard())
        return

    subscription_months_left = (panel_profile.expire.timestamp() - datetime.now().timestamp()) / 2592000

    filtered_goods = [good for good in goods.get() if good['months'] > subscription_months_left and good['type'] == 'update']
    if filtered_goods:
        min_good = min(filtered_goods, key=lambda good: good['months'])
        keyboard = await get_buy_menu_keyboard(callback.from_user.id, min_good['months'], "update")
        await callback.message.delete()
        await callback.message.answer(
            text=_("message_select_traffic_amount"),
            reply_markup=keyboard
        )
    else:
        await callback.answer(_("message_error"), reply_markup=get_main_menu_keyboard())

    await callback.answer()

@router.callback_query(F.data.startswith("pay_kassa_"))
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    data = callback.data.replace("pay_kassa_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return
    result = await yookassa.create_payment(
        callback.from_user.id,
        data,
        callback.from_user.language_code)
    sent_message = await callback.message.answer(
        _("To be paid – {amount} ₽ ⬇️").format(
            amount=int(result['amount'])
        ),
        reply_markup=get_pay_keyboard(result['url'], data))

    from db.methods import add_payment, PaymentPlatform
    await add_payment(callback.from_user.id, data, callback.from_user.language_code, result['payment_id'], PaymentPlatform.YOOKASSA, message_id=sent_message.message_id)

    await callback.answer()

@router.callback_query(F.data.startswith("pay_stars_"))
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    data = callback.data.replace("pay_stars_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return
    good = goods.get(data)
    discount = await get_user_promo_discount(callback.from_user.id)
    price = int(good['price']['stars'] * (1 - discount / 100))
    prices = [LabeledPrice(label="XTR", amount=price)]
    sent_message = await callback.message.answer_invoice(
        title = good['title'],
        currency="XTR",
        description=_("To be paid – {amount} ⭐️ ⬇️").format(
            amount=int(price)
        ),
        prices=prices,
        provider_token="",
        payload=data,
        reply_markup=get_xtr_pay_keyboard(data)
    )
    
    from db.methods import add_payment, PaymentPlatform
    await add_payment(callback.from_user.id, data, callback.from_user.language_code, data, PaymentPlatform.TELEGRAM, message_id=sent_message.message_id)
    
    await callback.answer()

@router.callback_query(F.data.startswith("pay_crypto_"))
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    data = callback.data.replace("pay_crypto_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return
    result = await cryptomus.create_payment(
        callback.from_user.id,
        data,
        callback.from_user.language_code)
    now = datetime.now()
    expire_date = (now + timedelta(minutes=60)).strftime("%d/%m/%Y, %H:%M")
    sent_message = await callback.message.answer(
        _("To be paid – {amount} $ ⬇️").format(
            amount=result['amount'],
            date=expire_date
        ),
        reply_markup=get_pay_keyboard(result['url'], data))

    from db.methods import add_payment, PaymentPlatform
    await add_payment(callback.from_user.id, data, callback.from_user.language_code, result['order_id'], PaymentPlatform.CRYPTOMUS, message_id=sent_message.message_id)

    await callback.answer()

@router.callback_query(F.data == ("trial"))
async def callback_trial(callback: CallbackQuery):
    result = await is_trial_available(callback.from_user.id)
    if not result:
        await callback.message.answer(
            _("message_subscription_access"),
            reply_markup=get_main_menu_keyboard())
        return
    result = await get_vpn_user(callback.from_user.id)
    panel = get_panel()
    panel_profile = await panel.generate_test_subscription(result.vpn_id)
    if not panel_profile:
        await callback.answer(_("message_error"), reply_markup=get_main_menu_keyboard())
        logging.error("Failed to generate test subscription for user %s", callback.from_user.id)
        return
    else:
        logging.info("Test subscription generated for user %s", callback.from_user.id)

    await start_trial(callback.from_user.id)
    subscription_url = panel_profile.subscription_url
    
    await callback.message.delete()
    
    await callback.message.answer(
        _("message_new_subscription_created"),
        reply_markup=get_install_subscription_keyboard(subscription_url)
    )
    await callback.answer()

@router.callback_query(F.data == "payment")
async def callback_payment(callback: CallbackQuery):
    keyboard = await get_months_keyboard(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(_("message_select_payment_period"), reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "faq")
async def callback_frequent_questions(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(_("message_frequent_questions").format(shop_name=glv.config['SHOP_NAME']), reply_markup=get_back_to_help_keyboard())
    await callback.answer()

# @router.callback_query(F.data == "tos")
# async def callback_terms_of_service(callback: CallbackQuery):
#     await callback.message.delete()
#     await callback.message.answer(text=_("message_terms_of_service"), reply_markup=get_back_to_help_keyboard())
#     await callback.answer()

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(text=_("message_select_action"), reply_markup=get_help_keyboard())
    await callback.answer()

@router.callback_query(F.data == "support")
async def callback_terms_of_service(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text=_("message_issue_prompt"), reply_markup=get_support_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data in goods.get_callbacks())
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    good = goods.get(callback.data)
    await callback.message.answer(text=_("message_select_payment_method"), reply_markup=get_payment_keyboard(good))
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    combined_message = _("message_welcome").format(name=callback.from_user.first_name) + "\n\n" + _("message_select_welcome_action")
    await callback.message.answer(combined_message, reply_markup=get_main_menu_keyboard(callback.from_user.language_code))
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def callback_back_to_profile(callback: CallbackQuery):
    await callback.message.delete()

    panel = get_panel()
    panel_profile = await panel.get_panel_user(callback.from_user.id)
    if panel_profile:
        url = panel_profile.subscription_url
        status = _(panel_profile.status)
        expire_date = panel_profile.expire.strftime("%d.%m.%Y") if panel_profile.expire else "∞"
        data_used = f"{panel_profile.used_traffic / 1073741824:.2f}"
        data_limit = f"{panel_profile.data_limit // 1073741824}" if panel_profile.data_limit else "∞"
        show_buy_traffic_button = panel_profile.data_limit and (panel_profile.used_traffic / panel_profile.data_limit) > 0.9
    else:
        url = ""
        status = "–"
        expire_date = "–"
        data_used = "–"
        data_limit = "–"
        show_buy_traffic_button = False

    from keyboards import get_user_profile_keyboard
    keyboard = await get_user_profile_keyboard(callback.from_user.id, show_buy_traffic_button, url)
    await callback.message.answer(
        text=_("subscription_data").format(
            status=status,
            expire_date=expire_date,
            data_used=data_used,
            data_limit=data_limit,
            link=glv.config['TG_INFO_CHANEL']
        ),
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_payment_"))
async def callback_back_to_payment(callback: CallbackQuery):
    await callback.message.delete()
    good_callback = callback.data.replace("back_to_payment_", "")
    good = goods.get(good_callback)
    await callback.message.answer(text=_("message_select_payment_method"), reply_markup=get_payment_keyboard(good))
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_traffic_"))
async def callback_back_to_traffic(callback: CallbackQuery):
    await callback.message.delete()
    parts = callback.data.replace("back_to_traffic_", "").split("_")
    purchase_type = parts[0]
    months = int(parts[1])

    keyboard = await get_buy_menu_keyboard(callback.from_user.id, months, purchase_type)

    if purchase_type == "renew":
        await callback.message.answer(text=_("message_traffic_renewal_info"), reply_markup=keyboard)
    else:
        await callback.message.answer(text=_("message_select_traffic_amount"), reply_markup=keyboard)

    await callback.answer()

def register_callbacks(dp: Dispatcher):
    dp.include_router(router)
