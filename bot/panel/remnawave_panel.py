from datetime import datetime, timedelta

from remnawave_api import RemnawaveSDK
from remnawave_api.models import UserResponseDto, UpdateUserRequestDto, CreateUserRequestDto

from .panel import Panel
from .models import PanelProfile
from db.methods import get_vpn_user

import glv

class RemnawavePanel(Panel):
    def __init__(self):
        self.api = RemnawaveSDK(base_url=glv.config['PANEL_HOST'], token=glv.config['REMNAWAVE_TOKEN'])
        
    async def check_if_user_exists(self, username) -> bool:
        try:
            await self.api.users.get_user_by_username(username)
            return True
        except Exception as e:
            return False
    
    async def get_panel_user(self, tg_id: int) -> PanelProfile:
            result = await get_vpn_user(tg_id)
            res = await self.check_if_user_exists(result.vpn_id)
            if not res:
                return None
            user: UserResponseDto = await self.api.users.get_user_by_username(result.vpn_id)
            return PanelProfile.from_UserResponseDto(user)
    
    async def generate_subscription(self, username: str, months: int, data_limit: int) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            user = await self.api.users.get_user_by_username(username)    
            user_update = UpdateUserRequestDto(uuid=user.uuid, status='ACTIVE', traffic_limit_bytes=data_limit)

            if user.expire_at < datetime.now():
                await self.api.users.reset_user_traffic(user.uuid)
                user_update.expire_at = datetime.now() + timedelta(days=months*30)
            else:
                user_update.expire_at = user.expire_at + timedelta(days=months*30)
            
            result = await self.api.users.update_user(user_update)
        else: 
            result = self.api.users.create_user(CreateUserRequestDto(
                username=username,
                expire_at=datetime.now() + timedelta(days=months*30),
                traffic_limit_bytes=data_limit,
                traffic_limit_strategy='MONTH',
                activate_all_inbounds=True
            ))        
        return PanelProfile.from_UserResponseDto(result)
    
    async def generate_test_subscription(self, username) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            user = await self.api.users.get_user_by_username(username)
            user_update = UpdateUserRequestDto(uuid=user.uuid, status='ACTIVE', traffic_limit_bytes=10737418240)

            if user.expire_at < datetime.now():
                user_update.expire_at = datetime.now() + timedelta(hours=glv.config['PERIOD_LIMIT'])
            else:
                user_update.expire_at = user.expire_at + timedelta(hours=glv.config['PERIOD_LIMIT'])
            result = await self.api.users.update_user(user_update)
        else:
            result = await self.api.users.create_user(CreateUserRequestDto(
                username=username,
                expire_at=datetime.now() + timedelta(hours=glv.config['PERIOD_LIMIT']),
                traffic_limit_bytes=10737418240,
                traffic_limit_strategy='MONTH',
                activate_all_inbounds=True
            ))        
        return PanelProfile.from_UserResponseDto(result)
    
    async def update_subscription_data_limit(self, username: str, data_limit: int) -> PanelProfile:
        if not await self.check_if_user_exists(username):
            return None
        user = await self.api.users.get_user_by_username(username)
        user_update = UpdateUserRequestDto(uuid=user.uuid, status='ACTIVE', traffic_limit_bytes=user.traffic_limit_bytes + data_limit)
        result = await self.api.users.update_user(user_update)
        return PanelProfile.from_UserResponseDto(result)
    
    async def reset_subscription_data_limit(self, username):
        if not await self.check_if_user_exists(username):
            return None
        user = await self.api.users.get_user_by_username(username)
        result = await self.api.users.reset_user_traffic(user.uuid)
        return PanelProfile.from_UserResponseDto(result)