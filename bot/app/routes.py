import ipaddress
import logging
from datetime import datetime
import hmac
import hashlib
import json

from aiohttp.web_request import Request
from aiohttp import web

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
    has_confirmed_payments
)
from keyboards import get_main_menu_keyboard, get_buy_more_traffic_keyboard, get_renew_subscription_keyboard, get_install_subscription_keyboard, get_payment_success_keyboard
from utils import webhook_data, goods
from utils import get_i18n_string
from panel import get_panel

import glv

YOOKASSA_IPS = (
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
)

async def check_crypto_payment(request: Request):
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    if client_ip not in ["91.227.144.54"]:
        return web.Response(status=403)
    data = await request.json()
    if not webhook_data.check(data, glv.config['CRYPTO_TOKEN']):
        return web.Response(status=403)
    payment = await get_payment(data['order_id'], PaymentPlatform.CRYPTOMUS)
    if payment == None:
        return web.Response()
    if data['status'] in ['paid', 'paid_over']:
        panel = get_panel()
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        if good['type'] == 'renew':
            is_trial = await is_test_subscription(payment.tg_id)
            if is_trial:
                await disable_trial(payment.tg_id)
            await panel.reset_subscription_data_limit(user.vpn_id)
            panel_profile = await panel.generate_subscription(username=user.vpn_id, months=good['months'], data_limit=good['data_limit'])
        else:
            panel_profile = await panel.update_subscription_data_limit(user.vpn_id, good['data_limit'])

        if payment.message_id:
            try:
                await glv.bot.delete_message(payment.tg_id, payment.message_id)
            except:
                pass

        if good['type'] == 'update':
            await glv.bot.send_message(payment.tg_id,
                get_i18n_string("message_payment_success", payment.lang),
                reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
            )
        else:
            await confirm_payment(payment.payment_id)
            user_has_payments = await has_confirmed_payments(payment.tg_id)
            if user_has_payments:
                await glv.bot.send_message(payment.tg_id,
                    get_i18n_string("message_payment_success", payment.lang),
                    reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
                )
            else:
                subscription_url = panel_profile.subscription_url
                await glv.bot.send_message(payment.tg_id,
                    get_i18n_string("message_new_subscription_created", payment.lang),
                    reply_markup=get_install_subscription_keyboard(subscription_url, payment.lang)
                )
        await use_all_promo_codes(payment.tg_id)
        await use_all_promo_codes(payment.tg_id)
    if data['status'] == 'cancel':
        await delete_payment(payment.payment_id)
    return web.Response()

async def check_yookassa_payment(request: Request):
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    f = True
    for subnet in YOOKASSA_IPS:
        if "/" in subnet:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(subnet):
                f = False
                break
        else:
            if client_ip == subnet:
                f = False
                break
    if f:
        return web.Response(status=403)
    data = (await request.json())['object']
    payment = await get_payment(data['id'], PaymentPlatform.YOOKASSA)
    if payment == None:
        return web.Response()
    if data['status'] in ['succeeded']:
        panel = get_panel()
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        if good['type'] == 'renew':
            is_trial = await is_test_subscription(payment.tg_id)
            if is_trial:
                await disable_trial(payment.tg_id)
            await panel.reset_subscription_data_limit(user.vpn_id)
            panel_profile = await panel.generate_subscription(username=user.vpn_id, months=good['months'], data_limit=good['data_limit'])
        else:
            panel_profile = await panel.update_subscription_data_limit(user.vpn_id, good['data_limit'])

        if payment.message_id:
            try:
                await glv.bot.delete_message(payment.tg_id, payment.message_id)
            except:
                pass

        if good['type'] == 'update':
            await glv.bot.send_message(payment.tg_id,
                get_i18n_string("message_payment_success", payment.lang),
                reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
            )
        else:
            await confirm_payment(payment.payment_id)
            user_has_payments = await has_confirmed_payments(payment.tg_id)
            if user_has_payments:
                await glv.bot.send_message(payment.tg_id,
                    get_i18n_string("message_payment_success", payment.lang),
                    reply_markup=get_payment_success_keyboard(payment.lang, payment.from_notification)
                )
            else:
                subscription_url = panel_profile.subscription_url
                await glv.bot.send_message(payment.tg_id,
                    get_i18n_string("message_new_subscription_created", payment.lang),
                    reply_markup=get_install_subscription_keyboard(subscription_url, payment.lang)
                )
        await use_all_promo_codes(payment.tg_id)
        await use_all_promo_codes(payment.tg_id)
    if data['status'] == 'canceled':
        await delete_payment(payment.payment_id)
    return web.Response()

async def notify_user(request: Request):
    from utils.ephemeral import EphemeralNotification

    if glv.config['PANEL_TYPE'] == 'MARZBAN':
        secret = request.headers.get('x-webhook-secret')

        if secret != glv.config['WEBHOOK_SECRET']:
            return web.Response(status=403)

        data = (await request.json())[0]
        if data['action'] not in ['reached_usage_percent', 'reached_days_left', 'user_expired', 'user_limited']:
            return web.Response()
        vpn_id = data["username"]
        user = await get_marzban_profile_by_vpn_id(vpn_id)
        if user is None:
            logging.info(f"No user found id={vpn_id}")
            return web.Response(status=404)
        chat_member = await glv.bot.get_chat_member(user.tg_id, user.tg_id)
        if chat_member is None:
            logging.info(f"No chat_member found id={user.tg_id}")
            return web.Response(status=404)
        action = data['action']
        message = ""
        keyboard = None
        match action:
            case "reached_usage_percent":
                usage_percent = int(data.get('usage_percent', 80))
                remaining_percent = 100 - usage_percent
                message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(name=chat_member.user.first_name, amount=remaining_percent)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case "reached_days_left":
                panel = get_panel()
                panel_profile = await panel.get_panel_user(user.tg_id)
                time_of_expiration = panel_profile.expire.strftime('%H:%M')
                message = get_i18n_string("message_reached_days_left", chat_member.user.language_code).format(name=chat_member.user.first_name, time=time_of_expiration)
                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case "user_expired":
                message = get_i18n_string("message_user_expired", chat_member.user.language_code).format(name=chat_member.user.first_name, link=glv.config['SUPPORT_LINK'])
                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case "user_limited":
                message = get_i18n_string("message_user_limited", chat_member.user.language_code).format(name=chat_member.user.first_name)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case _:
                return web.Response()

        msg_id = await EphemeralNotification.send_ephemeral(
            bot=glv.bot,
            chat_id=user.tg_id,
            text=message,
            reply_markup=keyboard,
            lang=chat_member.user.language_code,
            disable_web_page_preview=True
        )

        if msg_id:
            logging.info(f"Ephemeral notification {action} sent to user id={user.tg_id}, msg_id={msg_id}")
        else:
            logging.warning(f"Failed to send ephemeral notification {action} to user id={user.tg_id}")

    elif glv.config['PANEL_TYPE'] == 'REMNAWAVE':
        from utils.ephemeral import EphemeralNotification

        signature = request.headers.get('x-remnawave-signature')
        if not signature:
            return web.Response(status=403)
        payload = await request.json()
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
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
        if payload['event'] not in ['user.bandwidth_usage_threshold_reached', 'user.expires_in_24_hours', 'user.expires_in_48_hours', 'user.expires_in_72_hours', 'user.expired', 'user.limited']:
            return web.Response()
        vpn_id = payload['data']['username']
        user = await get_marzban_profile_by_vpn_id(vpn_id)
        if user is None:
            logging.info(f"No user found id={vpn_id}")
            return web.Response(status=404)
        chat_member = await glv.bot.get_chat_member(user.tg_id, user.tg_id)
        if chat_member is None:
            logging.info(f"No chat_member found id={user.tg_id}")
            return web.Response(status=404)
        event = payload['event']
        message = ""
        keyboard = None
        match event:
            case "user.bandwidth_usage_threshold_reached":
                threshold = int(payload['data'].get('threshold_percent', 80))
                remaining_percent = 100 - threshold
                message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(name=chat_member.user.first_name, amount=remaining_percent)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case s if s.startswith('user.expires_in'):
                panel = get_panel()
                panel_profile = await panel.get_panel_user(user.tg_id)
                time_of_expiration = panel_profile.expire.strftime('%H:%M')
                message = get_i18n_string("message_reached_days_left", chat_member.user.language_code).format(name=chat_member.user.first_name, time=time_of_expiration)
                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case "user.expired":
                message = get_i18n_string("message_user_expired", chat_member.user.language_code).format(name=chat_member.user.first_name, link=glv.config['SUPPORT_LINK'])
                keyboard = get_renew_subscription_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case "user.limited":
                message = get_i18n_string("message_user_limited", chat_member.user.language_code).format(name=chat_member.user.first_name)
                keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
            case _:
                return web.Response()

        msg_id = await EphemeralNotification.send_ephemeral(
            bot=glv.bot,
            chat_id=user.tg_id,
            text=message,
            reply_markup=keyboard,
            lang=chat_member.user.language_code,
            disable_web_page_preview=True
        )

        if msg_id:
            logging.info(f"Ephemeral notification {event} sent to user id={user.tg_id}, msg_id={msg_id}")
        else:
            logging.warning(f"Failed to send ephemeral notification {event} to user id={user.tg_id}")

    return web.Response()
