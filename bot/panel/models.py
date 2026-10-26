from pydantic import BaseModel
from datetime import datetime, UTC
from typing import Optional

import glv

class PanelProfile(BaseModel):
    username: str
    status: str
    subscription_url: str
    used_traffic: int
    data_limit: Optional[int] = None
    expire: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        return self.status == "expired" or (self.expire is not None and self.expire < datetime.now(UTC))
