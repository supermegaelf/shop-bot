from remnawave_api import RemnawaveSDK
import logging

import glv

base_url: str = glv.config['REMNAWAVE_BASE_URL']
token: str = glv.config['REMNAWAVE_TOKEN']

remnawave = RemnawaveSDK(base_url=base_url, token=token)

async def check_if_user_exists() -> bool:
    try:
        await remnawave.users.get_user_by_username("admin_admin")
        logging.info("exists")
        return True
    except:
        logging.info("not_exists")
        return False
    

# async def get_marzban_profile(tg_id: int):
#     result = await get_vpn_user(tg_id)
#     res = await check_if_user_exists(result.vpn_id)
#     if not res:
#         return None
#     return await panel.get_user(result.vpn_id)

# async def generate_test_subscription(username: str):
#     res = await check_if_user_exists(username)
#     if res:
#         user = await panel.get_user(username)
#         user['status'] = 'active'
#         if user['expire'] < time.time():
#             user['expire'] = get_test_subscription(glv.config['PERIOD_LIMIT'])
#         else:
#             user['expire'] += get_test_subscription(glv.config['PERIOD_LIMIT'], True)
#         result = await panel.modify_user(username, user)
#     else:
#         user = {
#             'username': username,
#             'proxies': ps["proxies"],
#             'inbounds': ps["inbounds"],
#             'expire': get_test_subscription(glv.config['PERIOD_LIMIT']),
#             'data_limit': 107374182400,
#             'data_limit_reset_strategy': "month",
#         }
#         result = await panel.add_user(user)
#     return result

# async def generate_marzban_subscription(username: str, good):
#     res = await check_if_user_exists(username)
#     if res:
#         user = await panel.get_user(username)
#         user['status'] = 'active'
#         if user['expire'] < time.time():
#             await panel.user_data_limit_reset(username)
#             user['expire'] = get_subscription_end_date(good['months'])   
#         else:
#             user['expire'] += get_subscription_end_date(good['months'], True)
#         user['data_limit'] = good['data_limit']
#         result = await panel.modify_user(username, user)
#     else:
#         user = {
#             'username': username,
#             'proxies': ps["proxies"],
#             'inbounds': ps["inbounds"],
#             'expire': get_subscription_end_date(good['months']),
#             'data_limit': good['data_limit'],
#             'data_limit_reset_strategy': "month",
#         }
#         result = await panel.add_user(user)
#     return result

# async def update_subscription_data_limit(username: str, good):
#     user = await panel.get_user(username)
#     user['status'] = 'active'
#     user['data_limit'] = user['data_limit'] + good['data_limit']
#     result = await panel.modify_user(username, user)
#     return result

# async def reset_data_limit(username: str):
#     if not await check_if_user_exists(username):
#         return None
#     result = await panel.user_data_limit_reset(username)
#     return result

# def get_test_subscription(hours: int, additional= False) -> int:
#     return (0 if additional else int(time.time())) + 60 * 60 * hours

# def get_subscription_end_date(months: int, additional = False) -> int:
#     return (0 if additional else int(time.time())) + 60 * 60 * 24 * 30 * months