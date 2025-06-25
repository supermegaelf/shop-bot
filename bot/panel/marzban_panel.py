import time

from bot.panel.panel import Panel
from utils.marzban_api import Marzban
import glv

class MarzbanPanel(Panel):
    def __init__(self):
        self.api = Marzban(glv.config['PANEL_HOST'], glv.config['PANEL_USER'], glv.config['PANEL_PASS'])
        
    async def check_if_user_exists(self, username):
        try:
            await self.api.get_user(username)
            return True
        except Exception as e:
            return False
    
    async def get_panel_user_by_tg_id(self, tg_id):
        return super().get_panel_user_by_tg_id()
    
    async def generate_subscription(self, username):
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
            result = await self.api.add_user(user)
        return result
    

    
    def generate_test_subscription(self, username):
        return super().generate_test_subscription()