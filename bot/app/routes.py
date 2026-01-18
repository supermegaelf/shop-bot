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
    has_confirmed_payments,
    get_last_traffic_notification,
    add_traffic_notification
)
from keyboards import get_main_menu_keyboard, get_buy_more_traffic_keyboard, get_renew_subscription_keyboard, get_install_subscription_keyboard, get_payment_success_keyboard
from utils import webhook_data, goods, referrals
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
                logging.debug(f"Failed to delete payment message {payment.message_id}: {e}")

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
                await glv.bot.send_message(
                    payment.tg_id,
                    get_i18n_string("message_payment_success", payment.lang),
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
        
        try:
            purchase_days = good["months"] * 30
            await referrals.apply_referral_bonuses(
                referee_id=payment.tg_id,
                purchase_days=purchase_days,
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
    if payload['event'] not in ['user.bandwidth_usage_threshold_reached', 'user.expires_in_24_hours', 'user.expired', 'user.limited', 'user.modified']:
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
        case "user.modified":
            user_traffic = payload['data'].get('userTraffic', {})
            used_traffic = user_traffic.get('usedTrafficBytes', 0)
            data_limit = payload['data'].get('trafficLimitBytes', 0)
            
            logging.info(f"user.modified: used={used_traffic}, limit={data_limit}")
            
            if not data_limit or data_limit <= 0:
                logging.warning(f"Invalid data_limit for user {user.tg_id}: {data_limit}")
                return web.Response()
            
            if used_traffic < 0:
                logging.warning(f"Negative used_traffic for user {user.tg_id}: {used_traffic}")
                return web.Response()
            
            if used_traffic and data_limit:
                traffic_usage = used_traffic / data_limit
                logging.info(f"Traffic usage for user {user.tg_id}: {traffic_usage*100:.1f}%")
                
                if traffic_usage > 0.75:
                    logging.info(f"Traffic threshold exceeded (>75%) for user {user.tg_id}")
                    last_notification = await get_last_traffic_notification(user.tg_id, "traffic_75_percent")
                    
                    if last_notification:
                        sent_at = last_notification.sent_at if hasattr(last_notification, 'sent_at') else last_notification._mapping.get('sent_at')
                        if sent_at:
                            time_since_last = datetime.now() - sent_at
                            logging.info(f"Last notification sent {time_since_last.total_seconds():.0f}s ago")
                            
                            if time_since_last.total_seconds() < 86400:
                                logging.info(f"Skipping notification (cooldown period)")
                                return web.Response()
                    
                    remaining_percent = 25
                    message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(
                        name=chat_member.user.first_name,
                        amount=remaining_percent
                    )
                    keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
                else:
                    logging.info(f"Traffic usage below threshold (<=75%), skipping notification")
                    return web.Response()
            else:
                logging.info(f"Missing traffic data: used={used_traffic}, limit={data_limit}")
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
                await add_traffic_notification(user.tg_id, "traffic_75_percent")
                logging.info(f"Ephemeral notification user.modified sent to user id={user.tg_id}, msg_id={msg_id}")
                from db.methods import save_user_message
                try:
                    await save_user_message(user.tg_id, msg_id, 'notification')
                except Exception as e:
                    logging.warning(f"Failed to save notification message to DB: {e}")
            else:
                logging.warning(f"Failed to send ephemeral notification user.modified to user id={user.tg_id}")
            
            return web.Response()
        case "user.bandwidth_usage_threshold_reached":
            threshold = int(payload['data'].get('threshold_percent', 80))
            remaining_percent = 100 - threshold
            message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(name=chat_member.user.first_name, amount=remaining_percent)
            keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
        case "user.expires_in_24_hours":
            panel = get_panel()
            panel_profile = await panel.get_panel_user(user.tg_id)
            if not panel_profile or not panel_profile.expire:
                return web.Response()
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
        from db.methods import save_user_message
        try:
            await save_user_message(user.tg_id, msg_id, 'notification')
        except Exception as e:
            logging.warning(f"Failed to save notification message to DB: {e}")
    else:
        logging.warning(f"Failed to send ephemeral notification {event} to user id={user.tg_id}")

    return web.Response()
