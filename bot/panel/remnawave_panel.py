import time

from remnawave_api import RemnawaveSDK
from remnawave_api.models import UserResponseDto

from panel.panel import Panel
from db.methods import get_vpn_user
from panel.models import PanelProfile

import glv

class RemnawavePanel(Panel):
    def __init__(self):
        self.api = RemnawaveSDK(base_url=glv.config['PANEL_HOST'], token=['REMNAWAVE_TOKEN'])
        
    async def check_if_user_exists(self, username):
        try:
            await self.api.users.get_user_by_username(username)
            return True
        except Exception as e:
            return False
    
    async def get_panel_user_by_tg_id(self, tg_id: int):
        try:
            user = await self.api.users.get_users_by_telegram_id(tg_id)
            return PanelProfile.from_UserResponseDto(user)
        except:
            result = await get_vpn_user(tg_id)
            res = await self.check_if_user_exists(result.vpn_id)
            if not res:
                return None
            user: UserResponseDto = await self.api.users.get_user_by_username(result.vpn_id)
            return PanelProfile.from_UserResponseDto(user)
    
    async def generate_subscription(self, username: str, months: int, data_limit: int):
        res = await self.check_if_user_exists(username)
        ps = self.get_protocols()
        if res:
            user: UserResponseDto = await self.api.users.get_user_by_username(username)
            if user.expire_at < time.time():
                await self.api.users.reset_user_traffic(user.uuid)
                expire_date = self.get_subscription_end_date(months)  
            else:
                user['expire'] += self.get_subscription_end_date(months, True)
            user['data_limit'] = data_limit
            result = await self.api.modify_user(username, user)
        else:
            user = {
                'username': username,
                'proxies': ps["proxies"],
                'inbounds': ps["inbounds"],
                'expire': self.get_subscription_end_date(months),
                'data_limit': data_limit,
                'data_limit_reset_strategy': "month",
            }
            result = await self.api.add_user(user)
        return result
    
    async def generate_test_subscription(self, username):
        res = await self.check_if_user_exists(username)
        ps = self.get_protocols()
        if res:
            user = await self.api.get_user(username)
            user['status'] = 'active'
            if user['expire'] < time.time():
                user['expire'] = self.get_test_subscription_end_date(glv.config['PERIOD_LIMIT'])
            else:
                user['expire'] += self.get_test_subscription_end_date(glv.config['PERIOD_LIMIT'], True)
            result = await self.api.modify_user(username, user)
        else:
            user = {
                'username': username,
                'proxies': ["proxies"],
                'inbounds': ps["inbounds"],
                'expire': self.get_test_subscription_end_date(glv.config['PERIOD_LIMIT']),
                'data_limit': 107374182400,
                'data_limit_reset_strategy': "month",
            }
            result = await self.api.users.create_user(user)
        return result
    
    async def reset_subscription_data_limit(self, username):
        if not await self.check_if_user_exists(username):
            return None
        result = await self.api.user_data_limit_reset(username)
        return result