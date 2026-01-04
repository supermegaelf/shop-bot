import logging

from aiogram import Router, Dispatcher, F
from aiogram.types import Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from utils import goods, MessageCleanup, try_delete_message
from db.methods import (
    get_vpn_user,
    add_payment,
    PaymentPlatform,
    is_test_subscription,
    disable_trial,
    use_all_promo_codes,
    has_confirmed_payments,
    get_payment,
)
from keyboards import (
    get_install_subscription_keyboard,
    get_payment_success_keyboard,
    get_main_menu_keyboard,
)
from panel import get_panel
import glv

router = Router(name="payment-router")


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    try:
        if goods.get(query.invoice_payload) is None:
            await query.answer(
                _("Error: Invalid product type.\nPlease contact the support team."),
                ok=False,
            )
            return
        await query.answer(ok=True)
    except Exception as e:
        logging.warning(f"Failed to answer pre_checkout_query {query.id}: {e}")


@router.message(F.successful_payment)
async def success_payment(message: Message, state: FSMContext):
    payment = await get_payment(
        message.successful_payment.invoice_payload, PaymentPlatform.TELEGRAM
    )

    if payment and payment.message_id:
        try:
            await glv.bot.delete_message(message.from_user.id, payment.message_id)
        except Exception as e:
            logging.debug(f"Failed to delete payment message {payment.message_id}: {e}")

    await try_delete_message(message)

    panel = get_panel()
    good = goods.get(message.successful_payment.invoice_payload)
    user = await get_vpn_user(message.from_user.id)

    from_notification = payment.from_notification if payment else False

    cleanup = MessageCleanup(glv.bot, state, glv.MESSAGE_CLEANUP_DEBUG)

    try:
        if good["type"] == "renew":
            is_trial = await is_test_subscription(message.from_user.id)
            if is_trial:
                await disable_trial(message.from_user.id)
            await panel.reset_subscription_data_limit(user.vpn_id)
            panel_profile = await panel.generate_subscription(
                username=user.vpn_id, months=good["months"], data_limit=good["data_limit"]
            )
        else:
            panel_profile = await panel.update_subscription_data_limit(
                user.vpn_id, good["data_limit"]
            )

        if panel_profile is None:
            raise Exception("Panel returned None profile")

        user_has_payments = await has_confirmed_payments(message.from_user.id)
        if user_has_payments:
            await cleanup.send_success(
                chat_id=message.from_user.id,
                text=_("message_payment_success"),
                reply_markup=get_payment_success_keyboard(
                    message.from_user.language_code, from_notification
                ),
            )
        else:
            subscription_url = panel_profile.subscription_url
            await cleanup.send_important(
                chat_id=message.from_user.id,
                text=_("message_new_subscription_created"),
                reply_markup=get_install_subscription_keyboard(
                    subscription_url, message.from_user.language_code
                ),
            )
    except Exception as e:
        logging.error(
            f"Failed to process subscription for user {message.from_user.id} after payment: {e}",
            exc_info=True
        )
        await add_payment(
            message.from_user.id,
            good["callback"],
            message.from_user.language_code,
            message.successful_payment.telegram_payment_charge_id,
            PaymentPlatform.TELEGRAM,
            False,
            from_notification=from_notification,
        )
        await cleanup.send_important(
            chat_id=message.from_user.id,
            text=_("message_error") + "\n\n" + _("Please contact support. Your payment has been registered."),
            reply_markup=get_main_menu_keyboard(user_id=message.from_user.id)
        )
        return

    await add_payment(
        message.from_user.id,
        good["callback"],
        message.from_user.language_code,
        message.successful_payment.telegram_payment_charge_id,
        PaymentPlatform.TELEGRAM,
        True,
        from_notification=from_notification,
    )
    await use_all_promo_codes(message.from_user.id)


def register_payments(dp: Dispatcher):
    dp.include_router(router)
