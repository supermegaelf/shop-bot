from datetime import datetime, timedelta, UTC
import httpx
import logging
from pydantic import ValidationError
from .panel import Panel
from .models import PanelProfile
from db.methods import get_vpn_user, get_marzban_profile_by_vpn_id
import glv

class RemnawavePanel(Panel):
    def __init__(self):
        headers = {
            'X-Forwarded-For': '127.0.0.1',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-Host': glv.config['PANEL_HOST'],
            'X-Real-IP': '127.0.0.1',
            'Authorization': f"Bearer {glv.config['REMNAWAVE_TOKEN']}"
        }
        api_base_url = f"{glv.config['PANEL_HOST']}/api"
        client = httpx.AsyncClient(headers=headers, base_url=api_base_url, timeout=5.0)
        self.client = client

    def _extract_used_traffic(self, user_data: dict) -> int:
        if 'usedTrafficBytes' in user_data:
            return user_data['usedTrafficBytes']
        if 'used_traffic_bytes' in user_data:
            return user_data['used_traffic_bytes']
        if 'userTraffic' in user_data and isinstance(user_data['userTraffic'], dict):
            return user_data['userTraffic'].get('usedTrafficBytes', 0)
        return 0

    async def _get_default_squad(self) -> dict | None:
        try:
            response = await self.client.get("/internal-squads")
            response.raise_for_status()
            data = response.json()
            squads = data['response']['internalSquads']
            for squad in squads:
                if squad['name'].lower() == 'default-squad':
                    return squad
            return None
        except Exception as e:
            raise Exception(f"Failed to fetch Default-Squad: {str(e)}")

    async def _get_user_by_username(self, username: str) -> dict | None:
        try:
            response = await self.client.get(f"/users/by-username/{username}")
            response.raise_for_status()
            data = response.json()
            return data.get('response')
        except Exception:
            return None

    async def check_if_user_exists(self, username) -> bool:
        try:
            response = await self.client.get(f"/users/by-username/{username}")
            response.raise_for_status()
            return True
        except Exception:
            return False

    async def get_panel_user(self, tg_id: int) -> PanelProfile:
        result = await get_vpn_user(tg_id)
        if result is None:
            return None
        try:
            response = await self.client.get(f"/users/by-username/{result.vpn_id}")
            response.raise_for_status()
            data = response.json()
            user_data = data.get('response')
            if not user_data:
                logging.warning(f"User {result.vpn_id} not found in API response")
                return None

            subscription_url = user_data.get('subscriptionUrl') or user_data.get('subscription_url') or ""

            return PanelProfile(
                username=user_data['username'],
                status=user_data['status'].lower(),
                subscription_url=subscription_url,
                used_traffic=self._extract_used_traffic(user_data),
                data_limit=user_data.get('trafficLimitBytes') or user_data.get('traffic_limit_bytes'),
                expire=datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00')) if user_data.get('expireAt') else None
            )
        except Exception as e:
            if "404" not in str(e):
                logging.error(f"Error getting user by username {result.vpn_id}: {e}")
            return None

    async def generate_subscription(self, username: str, months: int, data_limit: int) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            try:
                user_data = await self._get_user_by_username(username)
                if not user_data:
                    raise Exception("User not found in response")
                user_id = user_data['id']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    reset_response = await self.client.post(f"/users/{user_id}/actions/reset-traffic")
                    reset_response.raise_for_status()
                    new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                else:
                    new_expire_at = user_expire_at + timedelta(days=months*30)

                update_payload = {
                    'id': user_id,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': data_limit,
                    'trafficLimitStrategy': 'MONTH',
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                updated_user = updated_data['response']
                subscription_url = updated_user.get('subscriptionUrl') or updated_user.get('subscription_url') or ""
                return PanelProfile(
                    username=updated_user['username'],
                    status=updated_user['status'].lower(),
                    subscription_url=subscription_url,
                    used_traffic=self._extract_used_traffic(updated_user),
                    data_limit=updated_user.get('trafficLimitBytes') or updated_user.get('traffic_limit_bytes'),
                    expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
                )
            except Exception as e:
                raise
        else:
            try:
                new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                user_db = await get_marzban_profile_by_vpn_id(username)
                default_squad = await self._get_default_squad()
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': data_limit,
                    'trafficLimitStrategy': 'MONTH'
                }
                if default_squad:
                    create_payload['activeInternalSquads'] = [default_squad['uuid']]
                if user_db and user_db.tg_id:
                    create_payload['telegramId'] = user_db.tg_id
                create_response = await self.client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()
                created_user = created_data['response']

                subscription_url = created_user.get('subscriptionUrl') or created_user.get('subscription_url') or ""
                return PanelProfile(
                    username=created_user['username'],
                    status=created_user['status'].lower(),
                    subscription_url=subscription_url,
                    used_traffic=self._extract_used_traffic(created_user),
                    data_limit=created_user.get('trafficLimitBytes') or created_user.get('traffic_limit_bytes'),
                    expire=datetime.fromisoformat(created_user['expireAt'].replace('Z', '+00:00')) if created_user.get('expireAt') else None
                )
            except Exception as e:
                raise

    async def generate_test_subscription(self, username) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            try:
                user_data = await self._get_user_by_username(username)
                if not user_data:
                    raise Exception("User not found in response")
                user_id = user_data['id']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                else:
                    new_expire_at = user_expire_at + timedelta(hours=glv.config['PERIOD_LIMIT'])

                traffic_limit = glv.config['TRIAL_TRAFFIC_LIMIT']
                update_payload = {
                    'id': user_id,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': traffic_limit,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                updated_user = updated_data['response']
                subscription_url = updated_user.get('subscriptionUrl') or updated_user.get('subscription_url') or ""
                return PanelProfile(
                    username=updated_user['username'],
                    status=updated_user['status'].lower(),
                    subscription_url=subscription_url,
                    used_traffic=self._extract_used_traffic(updated_user),
                    data_limit=updated_user.get('trafficLimitBytes') or updated_user.get('traffic_limit_bytes'),
                    expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
                )
            except Exception as e:
                raise
        else:
            try:
                new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                traffic_limit = glv.config['TRIAL_TRAFFIC_LIMIT']
                user_db = await get_marzban_profile_by_vpn_id(username)
                default_squad = await self._get_default_squad()
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': traffic_limit,
                    'trafficLimitStrategy': 'MONTH'
                }
                if default_squad:
                    create_payload['activeInternalSquads'] = [default_squad['uuid']]
                if user_db and user_db.tg_id:
                    create_payload['telegramId'] = user_db.tg_id
                create_response = await self.client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()
                created_user = created_data['response']

                subscription_url = created_user.get('subscriptionUrl') or created_user.get('subscription_url') or ""
                return PanelProfile(
                    username=created_user['username'],
                    status=created_user['status'].lower(),
                    subscription_url=subscription_url,
                    used_traffic=self._extract_used_traffic(created_user),
                    data_limit=created_user.get('trafficLimitBytes') or created_user.get('traffic_limit_bytes'),
                    expire=datetime.fromisoformat(created_user['expireAt'].replace('Z', '+00:00')) if created_user.get('expireAt') else None
                )
            except Exception as e:
                raise

    async def update_subscription_data_limit(self, username: str, data_limit: int) -> PanelProfile:
        if not await self.check_if_user_exists(username):
            return None
        try:
            user_data = await self._get_user_by_username(username)
            if not user_data:
                raise Exception("User not found in response")
            user_id = user_data['id']
            current_limit = user_data.get('trafficLimitBytes', 0)

            update_payload = {
                'id': user_id,
                'status': 'ACTIVE',
                'trafficLimitBytes': current_limit + data_limit
            }
            update_response = await self.client.patch(f"/users", json=update_payload)
            update_response.raise_for_status()
            updated_data = update_response.json()

            updated_user = updated_data['response']
            return PanelProfile(
                username=updated_user['username'],
                status=updated_user['status'].lower(),
                subscription_url=updated_user['subscriptionUrl'],
                used_traffic=self._extract_used_traffic(updated_user),
                data_limit=updated_user.get('trafficLimitBytes'),
                expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
            )
        except Exception as e:
            raise

    async def set_subscription_data_limit(self, username: str, data_limit: int) -> PanelProfile:
        if not await self.check_if_user_exists(username):
            return None
        try:
            user_data = await self._get_user_by_username(username)
            if not user_data:
                raise Exception("User not found in response")
            user_id = user_data['id']

            update_payload = {
                'id': user_id,
                'status': 'ACTIVE',
                'trafficLimitBytes': data_limit
            }
            update_response = await self.client.patch(f"/users", json=update_payload)
            update_response.raise_for_status()
            updated_data = update_response.json()

            updated_user = updated_data['response']
            subscription_url = updated_user.get('subscriptionUrl') or updated_user.get('subscription_url') or ""
            return PanelProfile(
                username=updated_user['username'],
                status=updated_user['status'].lower(),
                subscription_url=subscription_url,
                used_traffic=self._extract_used_traffic(updated_user),
                data_limit=updated_user.get('trafficLimitBytes') or updated_user.get('traffic_limit_bytes'),
                expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
            )
        except Exception as e:
            raise

    async def reset_subscription_data_limit(self, username):
        if not await self.check_if_user_exists(username):
            return None
        try:
            user_data = await self._get_user_by_username(username)
            if not user_data:
                raise Exception("User not found in response")
            user_id = user_data['id']
            reset_response = await self.client.post(f"/users/{user_id}/actions/reset-traffic")
            reset_response.raise_for_status()
            reset_data = reset_response.json()
            reset_user = reset_data['response']
            subscription_url = reset_user.get('subscriptionUrl') or reset_user.get('subscription_url') or ""
            return PanelProfile(
                username=reset_user['username'],
                status=reset_user['status'].lower(),
                subscription_url=subscription_url,
                used_traffic=self._extract_used_traffic(reset_user),
                data_limit=reset_user.get('trafficLimitBytes') or reset_user.get('traffic_limit_bytes'),
                expire=datetime.fromisoformat(reset_user['expireAt'].replace('Z', '+00:00')) if reset_user.get('expireAt') else None
            )
        except Exception as e:
            raise

    async def update_user_telegram_id(self, username: str, tg_id: int) -> bool:
        try:
            user_data = None
            if await self.check_if_user_exists(username):
                user_data = await self._get_user_by_username(username)

            if not user_data:
                return False

            user_id = user_data['id']
            update_payload = {
                'id': user_id,
                'telegramId': tg_id
            }
            update_response = await self.client.patch(f"/users", json=update_payload)
            update_response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Failed to update telegram_id for user {username}: {e}")
            return False
