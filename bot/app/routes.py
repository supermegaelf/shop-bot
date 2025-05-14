import ipaddress
import logging

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
    use_all_promo_codes
)
from keyboards import get_main_menu_keyboard, get_buy_more_traffic_keyboard, get_renew_subscription_keyboard
from utils import webhook_data, goods, marzban_api
from utils import get_i18n_string
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
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        if good['type'] == 'renew':
            is_trial = await is_test_subscription(payment.tg_id)
            if is_trial:
                await marzban_api.reset_data_limit(user.vpn_id)
                await disable_trial(payment.tg_id)
            await marzban_api.generate_marzban_subscription(user.vpn_id, good)
        else:
            await marzban_api.update_subscription_data_limit(user.vpn_id, good)
        text = get_i18n_string("message_payment_success", payment.lang)
        await glv.bot.send_message(payment.tg_id,
            text.format(
                link=glv.config['TG_INFO_CHANEL']
            ),
            reply_markup=get_main_menu_keyboard(payment.lang)
        )
        await confirm_payment(payment.payment_id)
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
        good = goods.get(payment.callback)
        user = await get_vpn_user(payment.tg_id)
        if good['type'] == 'renew':
            is_trial = await is_test_subscription(payment.tg_id)
            if is_trial:
                await marzban_api.reset_data_limit(user.vpn_id)
                await disable_trial(payment.tg_id)
            await marzban_api.generate_marzban_subscription(user.vpn_id, good)
        else:
            await marzban_api.update_subscription_data_limit(user.vpn_id, good)
        text = get_i18n_string("Thank you for choice ❤️\n️\nSubscription is available in \"Access to VPN 🏄🏻‍♂️\" section.", payment.lang)
        await glv.bot.send_message(payment.tg_id,
            text.format(
                link=glv.config['TG_INFO_CHANEL']
            ),
            reply_markup=get_main_menu_keyboard(payment.lang)
        )
        await confirm_payment(payment.payment_id)
        await use_all_promo_codes(payment.tg_id)
    if data['status'] == 'canceled':
        await delete_payment(payment.payment_id)
    return web.Response()

async def notify_user(request: Request):
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
    match action:
        case "reached_usage_percent":
            message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(name=chat_member.user.first_name, amount=(100 - int(data['used_percent'])))
            await glv.bot.send_message(chat_id=user.tg_id, text=message, reply_markup=get_buy_more_traffic_keyboard(chat_member.user.language_code))
        case "reached_days_left":
            message = get_i18n_string("message_reached_days_left", chat_member.user.language_code).format(name=chat_member.user.first_name, days=int(data['days_left']))
            await glv.bot.send_message(chat_id=user.tg_id, text=message, reply_markup=get_renew_subscription_keyboard(chat_member.user.language_code))
        case "user_expired":
            message = get_i18n_string("message_user_expired", chat_member.user.language_code).format(name=chat_member.user.first_name, link=glv.config['SUPPORT_LINK'])
            await glv.bot.send_message(chat_id=user.tg_id, text=message, reply_markup=get_renew_subscription_keyboard(chat_member.user.language_code))
        case "user_limited":
            message = get_i18n_string("message_user_limited", chat_member.user.language_code).format(name=chat_member.user.first_name)
            await glv.bot.send_message(chat_id=user.tg_id, text=message, reply_markup=get_buy_more_traffic_keyboard(chat_member.user.language_code))
        case _:
            return web.Response()
           
    logging.info(f"Message {action} sent to user id={user.tg_id}.")
    return web.Response()
