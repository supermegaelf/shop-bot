from aiogram import Router, Dispatcher, F
from aiogram.types import Message, PreCheckoutQuery
from aiogram.utils.i18n import gettext as _

from utils import goods, marzban_api
from db.methods import get_vpn_user, add_payment, PaymentPlatform, is_test_subscription, disable_trial, use_all_promo_codes
from keyboards import get_main_menu_keyboard

import glv

router = Router(name="payment-router")

@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    if goods.get(query.invoice_payload) is None:
        return await query.answer(_("Error: Invalid product type.\nPlease contact the support team."), ok = False)
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def success_payment(message: Message):
    good = goods.get(message.successful_payment.invoice_payload)
    user = await get_vpn_user(message.from_user.id)
    if good['type'] == 'renew':
        is_trial = await is_test_subscription(message.from_user.id)
        if is_trial:
            await marzban_api.reset_data_limit(user.vpn_id)
            await disable_trial(message.from_user.id)
        await marzban_api.generate_marzban_subscription(user.vpn_id, good)
    else:
        await marzban_api.update_subscription_data_limit(user.vpn_id, good)
    
    await add_payment(message.from_user.id, good['callback'], message.from_user.language_code, message.successful_payment.telegram_payment_charge_id, PaymentPlatform.TELEGRAM, True)
    await use_all_promo_codes(message.from_user.id)
    await message.answer(
        text = _("Thank you for choice ❤️\n️\nSubscription is available in \"Access to VPN 🏄🏻‍♂️\" section.").format(
            link=glv.config['TG_INFO_CHANEL']),
        reply_markup=get_main_menu_keyboard())
    
def register_payments(dp: Dispatcher):
    dp.include_router(router)