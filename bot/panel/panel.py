import time
from abc import ABC, abstractmethod

from .models import PanelProfile
import glv

PROTOCOLS = {
        "vmess": [
            {},
            ["VMess TCP"]
        ],
        "vless": [
            {
                "flow": "xtls-rprx-vision"
            },
            ["VLESS Reality Steal Oneself", "VLESS WS"]
        ],
        "trojan": [
            {},
            ["Trojan Websocket TLS"]
        ],
        "shadowsocks": [
            {
                "method": "chacha20-ietf-poly1305"
            },
            ["Shadowsocks TCP"]
        ]
    }

class Panel(ABC):
    @abstractmethod
    async def check_if_user_user_exists(self, username: str) -> bool:
        pass

    @abstractmethod
    async def get_panel_user_by_tg_id(self, tg_id: int) -> PanelProfile:
        pass
    
    @abstractmethod
    async def generate_subscription(self, username: str) -> PanelProfile:
        pass

    @abstractmethod
    async def generate_test_subscription(self, username: str) -> PanelProfile:
        pass

    @abstractmethod
    async def update_subscription_data_limit(self, username: str, data_limit: int):
        pass

    @abstractmethod
    async def reset_subscription_data_limit(self, username: str):
        pass
    
    @staticmethod
    def get_subscription_end_date(months: int, additional = False) -> int:
        return (0 if additional else int(time.time())) + 60 * 60 * 24 * 30 * months
    
    @staticmethod
    def get_test_subscription_end_date(hours: int, additional= False) -> int:
        return (0 if additional else int(time.time())) + 60 * 60 * hours
    
    @staticmethod
    def get_protocols() -> dict:
        proxies = {}
        inbounds = {}
        
        for proto in glv.config['PROTOCOLS']:
            l = proto.lower()
            if l not in PROTOCOLS:
                continue
            proxies[l] = PROTOCOLS[l][0]
            inbounds[l] = PROTOCOLS[l][1]
        return {
            "proxies": proxies,
            "inbounds": inbounds
        }
        

    

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