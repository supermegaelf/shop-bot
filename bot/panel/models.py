from pydantic import BaseModel

from remnawave_api.models import UserResponseDto
import glv

class PanelProfile(BaseModel):
    username: str
    status: str
    subscription_url: str
    used_traffic: int
    data_limit: int

    @classmethod
    def from_UserResponseDto(user: UserResponseDto):
        return PanelProfile(
            username=user.username,
            status=user.status.lower(),
            subscription_url=user.subscription_url,
            used_traffic=user.used_traffic_bytes,
            data_limit=user.traffic_limit_bytes
        )
    
    @classmethod
    def fromMarzbanProfile(marzban_profile: dict):
        return PanelProfile(
            username=marzban_profile.get('username'),
            status=marzban_profile.get('status'),
            subscription_url=glv.config['PANEL_GLOBAL'] + marzban_profile.get('subscription_url'),
            used_traffic=marzban_profile.get('used_traffic'),
            data_limit=marzban_profile.get('data_limit')
        )

