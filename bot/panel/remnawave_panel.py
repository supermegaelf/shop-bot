import time
from datetime import datetime, timedelta

from remnawave_api import RemnawaveSDK
from remnawave_api.models import UserResponseDto, UpdateUserRequestDto, CreateUserRequestDto

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
        if res:
            user: UserResponseDto = await self.api.users.get_user_by_username(username)    
            user_update: UpdateUserRequestDto = UpdateUserRequestDto(uuid=user.uuid, status='ACTIVE', traffic_limit_bytes=data_limit)

            if user.expire_at < datetime.now():
                await self.api.users.reset_user_traffic(user.uuid)
                user_update.expire_at = datetime.now() + timedelta(days=months*30)
            else:
                user_update.expire_at = user.expire_at + timedelta(days=months*30)
            
            result: UserResponseDto = await self.api.users.update_user(username, user)
        else: 
            result: UserResponseDto = self.api.users.create_user(CreateUserRequestDto(
                username=username,
                expire_at=datetime.now() + timedelta(days=months*30),
                data_limit=data_limit,
                traffic_limit_strategy='MONTH'
            ))        
        return PanelProfile.from_UserResponseDto(result)
    
    async def generate_test_subscription(self, username):
        res = await self.check_if_user_exists(username)
        ps = self.get_protocols()
        if res:
            user: UserResponseDto = await self.api.users.get_user_by_username(username)
            user_update: UpdateUserRequestDto = UpdateUserRequestDto(uuid=user.uuid, status='ACTIVE', traffic_limit_bytes=10737418240)

            if user.expire_at < datetime.now():
                user_update.expire_at = datetime.now() + timedelta(hours=glv.config['PERIOD_LIMIT'])
            else:
                user_update.expire_at = user.expire_at + timedelta(hours=glv.config['PERIOD_LIMIT'])
            result: UserResponseDto = await self.api.users.update_user(username, user)
        else:
            result: UserResponseDto = self.api.users.create_user(CreateUserRequestDto(
                username=username,
                expire_at=datetime.now() + timedelta(hours=glv.config['PERIOD_LIMIT']),
                data_limit=10737418240,
                traffic_limit_strategy='MONTH'
            ))        
        return PanelProfile.from_UserResponseDto(result)
    
    async def reset_subscription_data_limit(self, username):
        if not await self.check_if_user_exists(username):
            return None
        result = await self.api.user_data_limit_reset(username)
        return result