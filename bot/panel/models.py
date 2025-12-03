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
    
