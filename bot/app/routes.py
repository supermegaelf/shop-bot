import asyncio
import ipaddress
import logging
from datetime import datetime, timedelta
import hmac
import hashlib
import json

from aiohttp.web_request import Request
from aiohttp import web
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.methods import (
    get_vpn_user,
    get_marzban_profile_by_vpn_id,
    get_payment,
    delete_payment,
    confirm_payment,
    PaymentPlatform,
    disable_trial,
    is_test_subscription,
    use_all_promo_codes,
    has_confirmed_payments,
    get_last_traffic_notification,
    add_traffic_notification
)
from keyboards import get_main_menu_keyboard, get_buy_more_traffic_keyboard, get_renew_subscription_keyboard, get_install_subscription_keyboard, get_payment_success_keyboard
from utils import webhook_data, goods, referrals
from utils import get_i18n_string
from panel import get_panel

import glv

_background_tasks: set = set()

YOOKASSA_IPS = (
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
)


async def _process_payment_success(payment, good, user):
    panel = get_panel()
    
    try:
        if good['type'] == 'renew':
            is_trial = await is_test_subscription(payment.tg_id)
            if is_trial:
                await disable_trial(payment.tg_id)
            await panel.reset_subscription_data_limit(user.vpn_id)
            panel_profile = await panel.generate_subscription(
                username=user.vpn_id, 
                months=good['months'], 
                data_limit=good['data_limit']
            )
        else:
            panel_profile = await panel.update_subscription_data_limit(user.vpn_id, good['data_limit'])

        if panel_profile is None:
            raise Exception("Panel returned None profile")

        if payment.message_id:
            try:
                await glv.bot.delete_message(payment.tg_id, payment.message_id)
            except Exception as e:
                logging.warning(f"Failed to delete payment message {payment.message_id} for user {payment.tg_id}: {e}")

        referee_bonus_days = 0
        if good.get("type") == "renew" and "months" in good:
            purchase_days = good["months"] * 30
            referee_bonus_days = await referrals.get_referee_bonus_days(payment.tg_id, purchase_days)

        if good['type'] == 'update':
            await glv.bot.send_message(
                payment.tg_id,
                get_i18n_string("message_payment_success", payment.lang),
                reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
            )
        else:
            await confirm_payment(payment.payment_id)
            user_has_payments = await has_confirmed_payments(payment.tg_id)
            if user_has_payments:
                if referee_bonus_days > 0:
                    text = get_i18n_string("message_payment_success_with_bonus", payment.lang).format(days=referee_bonus_days)
                else:
                    text = get_i18n_string("message_payment_success", payment.lang)
                await glv.bot.send_message(
                    payment.tg_id,
                    text,
                    reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
                )
            else:
                subscription_url = panel_profile.subscription_url
                await glv.bot.send_message(
                    payment.tg_id,
                    get_i18n_string("message_new_subscription_created", payment.lang),
                    reply_markup=get_install_subscription_keyboard(subscription_url, payment.lang)
                )

        await use_all_promo_codes(payment.tg_id)

        if good.get("type") == "renew" and "months" in good:
            try:
                await referrals.apply_referral_bonuses(
                    referee_id=payment.tg_id,
                    purchase_days=purchase_days,
                    payment_id=payment.id,
                    lang=payment.lang or 'ru'
                )
            except Exception as ref_error:
                logging.error(f"Failed to apply referral bonuses for user {payment.tg_id}: {ref_error}")
    except Exception as e:
        logging.error(
            f"Failed to process subscription for user {payment.tg_id} after payment {payment.payment_id}: {e}",
            exc_info=True
        )
        error_text = get_i18n_string("message_error", payment.lang)
        support_link = glv.config.get('SUPPORT_LINK', '')
        if support_link:
            error_text += f"\n\nPlease contact support. Your payment has been registered."
        try:
            await glv.bot.send_message(
                payment.tg_id,
                error_text
            )
        except Exception:
            pass

async def check_crypto_payment(request: Request):
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    if client_ip not in ["91.227.144.54"]:
        return web.Response(status=403)
    data = await request.json()
    if not webhook_data.check(data, glv.config['CRYPTO_TOKEN']):
        return web.Response(status=403)
    payment = await get_payment(data['order_id'], PaymentPlatform.CRYPTOMUS)
    if payment is None:
        return web.Response()
    
    if data['status'] in ['paid', 'paid_over']:
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        await _process_payment_success(payment, good, user)
    
    if data['status'] == 'cancel':
        await delete_payment(payment.payment_id)
    
    return web.Response()

def _check_ip_in_subnets(client_ip: str, subnets: tuple) -> bool:
    for subnet in subnets:
        if "/" in subnet:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(subnet):
                return True
        else:
            if client_ip == subnet:
                return True
    return False


async def check_yookassa_payment(request: Request):
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    if not _check_ip_in_subnets(client_ip, YOOKASSA_IPS):
        return web.Response(status=403)
    
    data = (await request.json())['object']
    payment = await get_payment(data['id'], PaymentPlatform.YOOKASSA)
    if payment is None:
        return web.Response()
    
    if data['status'] in ['succeeded']:
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        await _process_payment_success(payment, good, user)
    
    if data['status'] == 'canceled':
        await delete_payment(payment.payment_id)
    
    return web.Response()

async def notify_user(request: Request):
    signature = request.headers.get('x-remnawave-signature')
    if not signature:
        return web.Response(status=403)
    payload_bytes = await request.read()
    payload = json.loads(payload_bytes)
    logging.info(f"payload: {payload}")
    webhook_secret = str(glv.config['WEBHOOK_SECRET']).encode('utf-8')
    computed_signature = hmac.new(
        key=webhook_secret,
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    logging.info(f"sign: {signature}, computed:{computed_signature}")
    if not hmac.compare_digest(signature, computed_signature):
        return web.Response(status=403)
    if payload['event'] not in ['user.bandwidth_usage_threshold_reached', 'user.expiration', 'user.expired', 'user.limited', 'user.not_connected']:
        return web.Response()
    vpn_id = payload['data']['username']
    user = await get_marzban_profile_by_vpn_id(vpn_id)
    if user is None:
        logging.info(f"No user found id={vpn_id}")
        return web.Response(status=404)

    task = asyncio.create_task(_process_notification(payload, user))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return web.Response()


async def _process_notification(payload: dict, user) -> None:
    from utils.ephemeral import EphemeralNotification
    from db.methods import save_user_message

    event = payload['event']

    try:
        chat_member = await asyncio.wait_for(
            glv.bot.get_chat_member(user.tg_id, user.tg_id),
            timeout=10.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Failed to get chat member for user {user.tg_id}: {e}")
        return

    message = ""
    keyboard = None

    try:
        match event:
            case "user.bandwidth_usage_threshold_reached":
                threshold = int(payload['data'].get('lastTriggeredThreshold', 75))
                notification_type = f"traffic_{threshold}_percent"

                last_notification = await get_last_traffic_notification(user.tg_id, notification_type)
                if last_notification:
                    sent_at = last_notification.sent_at if hasattr(last_notification, 'sent_at') else last_notification._mapping.get('sent_at')
                    if sent_at and (datetime.now() - sent_at).total_seconds() < 86400:
                        logging.info(f"Skipping notification (cooldown period)")
                        return

                remaining_percent = 100 - threshold
                message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(name=chat_member.user.first_name, amount=remaining_percent)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)

            case "user.expiration":
                expiration_hours = (payload.get('meta') or {}).get('expiration')
                if expiration_hours is None:
                    return

                panel = get_panel()
                panel_profile = await panel.get_panel_user(user.tg_id)
                if not panel_profile or not panel_profile.expire:
                    return

                msk_offset = timedelta(hours=3)
                time_of_expiration = (panel_profile.expire + msk_offset).strftime('%H:%M')

                if expiration_hours == -24:
                    message = get_i18n_string("message_reached_days_left", chat_member.user.language_code).format(name=chat_member.user.first_name, time=time_of_expiration)
                elif expiration_hours == -48:
                    message = get_i18n_string("message_expires_in_48_hours", chat_member.user.language_code).format(name=chat_member.user.first_name, time=time_of_expiration)
                elif expiration_hours == -72:
                    message = get_i18n_string("message_expires_in_72_hours", chat_member.user.language_code).format(name=chat_member.user.first_name, time=time_of_expiration)
                else:
                    logging.info(f"Unhandled expiration offset {expiration_hours}h for user {user.tg_id}")
                    return

                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)

            case "user.expired":
                message = get_i18n_string("message_user_expired", chat_member.user.language_code).format(name=chat_member.user.first_name, link=glv.config['SUPPORT_LINK'])
                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)

            case "user.limited":
                message = get_i18n_string("message_user_limited", chat_member.user.language_code).format(name=chat_member.user.first_name)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)

            case "user.not_connected":
                if not await is_test_subscription(user.tg_id):
                    return
                panel = get_panel()
                panel_profile = await panel.get_panel_user(user.tg_id)
                if not panel_profile or not panel_profile.subscription_url:
                    logging.info(f"No panel profile or subscription_url for user {user.tg_id}, skipping not_connected notification")
                    return
                message = get_i18n_string("message_not_connected", chat_member.user.language_code).format(
                    name=chat_member.user.first_name,
                    link=glv.config['SUPPORT_LINK']
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=get_i18n_string("button_install", chat_member.user.language_code),
                        url=panel_profile.subscription_url
                    )
                ]])

            case _:
                return

        msg_id = await asyncio.wait_for(
            EphemeralNotification.send_ephemeral(
                bot=glv.bot,
                chat_id=user.tg_id,
                text=message,
                reply_markup=keyboard,
                lang=chat_member.user.language_code,
                disable_web_page_preview=True
            ),
            timeout=10.0
        )

        if msg_id:
            logging.info(f"Ephemeral notification {event} sent to user id={user.tg_id}, msg_id={msg_id}")

            if event == "user.bandwidth_usage_threshold_reached":
                await add_traffic_notification(user.tg_id, notification_type)

            try:
                await save_user_message(user.tg_id, msg_id, 'notification')
            except Exception as e:
                logging.warning(f"Failed to save notification message to DB: {e}")
        else:
            logging.warning(f"Failed to send ephemeral notification {event} to user id={user.tg_id}")

    except asyncio.TimeoutError:
        logging.warning(f"Timeout processing notification {event} for user {user.tg_id}")
    except Exception as e:
        logging.error(f"Error processing notification {event} for user {user.tg_id}: {e}", exc_info=True)
