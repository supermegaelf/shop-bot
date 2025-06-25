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
    async def check_if_user_exists(self, username: str) -> bool:
        pass

    @abstractmethod
    async def get_panel_user(self, tg_id: int) -> PanelProfile:
        pass
    
    @abstractmethod
    async def generate_subscription(self, username: str, months: int, data_limit: int) -> PanelProfile:
        pass

    @abstractmethod
    async def generate_test_subscription(self, username: str) -> PanelProfile:
        pass

    @abstractmethod
    async def update_subscription_data_limit(self, username: str, data_limit: int) -> PanelProfile:
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
