from pydantic import BaseModel
from datetime import datetime
from typing import Optional

import glv

class PanelProfile(BaseModel):
    username: str
    status: str
    subscription_url: str
    used_traffic: int
    data_limit: Optional[int] = None
    expire: Optional[datetime] = None
