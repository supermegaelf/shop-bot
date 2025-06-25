from utils import marzban_api
from panel import get_panel
from panel.marzban_panel import MarzbanPanel

async def update_marzban_token():
    panel: MarzbanPanel = get_panel()
    panel.api.get_token()