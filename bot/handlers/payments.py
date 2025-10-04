from aiogram import Router, Dispatcher, F
from aiogram.types import Message, PreCheckoutQuery
from aiogram.utils.i18n import gettext as _

from utils import goods
from db.methods import get_vpn_user, add_payment, PaymentPlatform, is_test_subscription, disable_trial, use_all_promo_codes, has_confirmed_payments
from keyboards import get_main_menu_keyboard, get_install_subscription_keyboard
from panel import get_panel

import glv

router = Router(name="payment-router")

@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    if goods.get(query.invoice_payload) is None:
        return await query.answer(_("Error: Invalid product type.\nPlease contact the support team."), ok = False)
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def success_payment(message: Message):
    panel = get_panel()
    good = goods.get(message.successful_payment.invoice_payload)
    user = await get_vpn_user(message.from_user.id)
    if good['type'] == 'renew':
        is_trial = await is_test_subscription(message.from_user.id)
        if is_trial:
            await disable_trial(message.from_user.id)
        await panel.reset_subscription_data_limit(user.vpn_id)
        marzban_profile = await panel.generate_subscription(username=user.vpn_id, months=good['months'], data_limit=good['data_limit'])
    else:
        marzban_profile = await panel.update_subscription_data_limit(user.vpn_id, good['data_limit'])

    user_has_payments = await has_confirmed_payments(message.from_user.id)
    if user_has_payments:
        await glv.bot.send_message(message.from_user.id,
            _("message_payment_success"),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        subscription_url = glv.config['PANEL_GLOBAL'] + marzban_profile['subscription_url']
        await glv.bot.send_message(message.from_user.id,
            _("message_new_subscription_created"),
            reply_markup=get_install_subscription_keyboard(subscription_url)
        )
    
    await add_payment(message.from_user.id, good['callback'], message.from_user.language_code, message.successful_payment.telegram_payment_charge_id, PaymentPlatform.TELEGRAM, True)
    await use_all_promo_codes(message.from_user.id)
    
def register_payments(dp: Dispatcher):
    dp.include_router(router)
