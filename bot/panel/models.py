from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from remnawave_api.models import UserResponseDto

import glv

class PanelProfile(BaseModel):
    username: str
    status: str
    subscription_url: str
    used_traffic: int
    data_limit: Optional[int] = None
    expire: Optional[datetime] = None
    
    @classmethod
    def from_UserResponseDto(cls, user: UserResponseDto):
        return cls(
            username=user.username,
            status=user.status.lower(),
            subscription_url=user.subscription_url,
            used_traffic=user.used_traffic_bytes,
            data_limit=user.traffic_limit_bytes,
            expire=user.expire_at
        )
    
    @classmethod
    def from_marzban_profile(cls, marzban_profile: dict):
        return cls(
            username=marzban_profile.get('username'),
            status=marzban_profile.get('status'),
            subscription_url=glv.config['PANEL_GLOBAL'] + marzban_profile.get('subscription_url'),
            used_traffic=marzban_profile.get('used_traffic'),
            data_limit=marzban_profile.get('data_limit'),
            expire=datetime.fromtimestamp(marzban_profile.get('expire')) if marzban_profile.get('expire') else None
        )
