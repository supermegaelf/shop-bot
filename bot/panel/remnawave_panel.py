from datetime import datetime, timedelta, UTC
import httpx
from pydantic import ValidationError
from .panel import Panel
from .models import PanelProfile
from db.methods import get_vpn_user
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
        client = httpx.AsyncClient(headers=headers, base_url=api_base_url, timeout=30.0)
        self.client = client

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

    async def _add_user_to_squad(self, user_uuid: str, squad_uuid: str, inbound_uuids: list[str]) -> bool:
        try:
            response = await self.client.get(f"/internal-squads/{squad_uuid}")
            response.raise_for_status()
            data = response.json()
            squad = data['response']
            current_users = squad.get('users', [])

            if user_uuid in current_users:
                return True

            add_users_payload = {
                'users': [user_uuid]
            }

            update_response = await self.client.post(
                f"/internal-squads/{squad_uuid}/bulk-actions/add-users",
                json=add_users_payload
            )
            update_response.raise_for_status()
            updated_data = update_response.json()

            verify_response = await self.client.get(f"/internal-squads/{squad_uuid}")
            verify_response.raise_for_status()
            verify_data = verify_response.json()

            return True
        except Exception as e:
            raise Exception(f"Failed to add user to squad: {str(e)}")

    async def check_if_user_exists(self, username) -> bool:
        try:
            response = await self.client.get(f"/users?username={username}")
            response.raise_for_status()
            data = response.json()
            users = data['response']['users']
            for user in users:
                if user['username'] == username:
                    return True
            return False
        except Exception as e:
            return False

    async def get_panel_user(self, tg_id: int) -> PanelProfile:
        result = await get_vpn_user(tg_id)
        res = await self.check_if_user_exists(result.vpn_id)
        if not res:
            return None
        try:
            response = await self.client.get(f"/users?username={result.vpn_id}")
            response.raise_for_status()
            data = response.json()
            user_data = None
            for user in data['response']['users']:
                if user['username'] == result.vpn_id:
                    user_data = user
                    break
            if not user_data:
                return None
            return PanelProfile(
                username=user_data['username'],
                status=user_data['status'].lower(),
                subscription_url=user_data['subscriptionUrl'],
                used_traffic=user_data['usedTrafficBytes'],
                data_limit=user_data.get('trafficLimitBytes'),
                expire=datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00')) if user_data.get('expireAt') else None
            )
        except Exception as e:
            return None

    async def generate_subscription(self, username: str, months: int, data_limit: int) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            try:
                response = await self.client.get(f"/users?username={username}")
                response.raise_for_status()
                data = response.json()
                user_data = None
                for user in data['response']['users']:
                    if user['username'] == username:
                        user_data = user
                        break
                if not user_data:
                    raise Exception("User not found in response")
                user_uuid = user_data['uuid']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    reset_response = await self.client.post(f"/users/{user_uuid}/reset-traffic")
                    reset_response.raise_for_status()
                    new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                else:
                    new_expire_at = user_expire_at + timedelta(days=months*30)

                update_payload = {
                    'uuid': user_uuid,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': data_limit,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                updated_user = updated_data['response']
                return PanelProfile(
                    username=updated_user['username'],
                    status=updated_user['status'].lower(),
                    subscription_url=updated_user['subscriptionUrl'],
                    used_traffic=updated_user['usedTrafficBytes'],
                    data_limit=updated_user.get('trafficLimitBytes'),
                    expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
                )
            except Exception as e:
                raise
        else:
            try:
                new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': data_limit,
                    'trafficLimitStrategy': 'MONTH',
                    'activateAllInbounds': True
                }
                create_response = await self.client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()
                created_user = created_data['response']

                default_squad = await self._get_default_squad()
                if default_squad:
                    inbound_uuids = [inbound['uuid'] for inbound in default_squad['inbounds']]
                    await self._add_user_to_squad(
                        user_uuid=created_user['uuid'],
                        squad_uuid=default_squad['uuid'],
                        inbound_uuids=inbound_uuids
                    )

                return PanelProfile(
                    username=created_user['username'],
                    status=created_user['status'].lower(),
                    subscription_url=created_user['subscriptionUrl'],
                    used_traffic=created_user['usedTrafficBytes'],
                    data_limit=created_user.get('trafficLimitBytes'),
                    expire=datetime.fromisoformat(created_user['expireAt'].replace('Z', '+00:00')) if created_user.get('expireAt') else None
                )
            except Exception as e:
                raise

    async def generate_test_subscription(self, username) -> PanelProfile:
        res = await self.check_if_user_exists(username)
        if res:
            try:
                response = await self.client.get(f"/users?username={username}")
                response.raise_for_status()
                data = response.json()
                user_data = None
                for user in data['response']['users']:
                    if user['username'] == username:
                        user_data = user
                        break
                if not user_data:
                    raise Exception("User not found in response")
                user_uuid = user_data['uuid']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                else:
                    new_expire_at = user_expire_at + timedelta(hours=glv.config['PERIOD_LIMIT'])

                traffic_limit = glv.config.get('DEFAULT_TRAFFIC_LIMIT', 10737418240)
                update_payload = {
                    'uuid': user_uuid,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': traffic_limit,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                updated_user = updated_data['response']
                return PanelProfile(
                    username=updated_user['username'],
                    status=updated_user['status'].lower(),
                    subscription_url=updated_user['subscriptionUrl'],
                    used_traffic=updated_user['usedTrafficBytes'],
                    data_limit=updated_user.get('trafficLimitBytes'),
                    expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
                )
            except Exception as e:
                raise
        else:
            try:
                new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                traffic_limit = glv.config.get('DEFAULT_TRAFFIC_LIMIT', 10737418240)
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': traffic_limit,
                    'trafficLimitStrategy': 'MONTH',
                    'activateAllInbounds': True
                }
                create_response = await self.client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()
                created_user = created_data['response']

                default_squad = await self._get_default_squad()
                if default_squad:
                    inbound_uuids = [inbound['uuid'] for inbound in default_squad['inbounds']]
                    await self._add_user_to_squad(
                        user_uuid=created_user['uuid'],
                        squad_uuid=default_squad['uuid'],
                        inbound_uuids=inbound_uuids
                    )

                return PanelProfile(
                    username=created_user['username'],
                    status=created_user['status'].lower(),
                    subscription_url=created_user['subscriptionUrl'],
                    used_traffic=created_user['usedTrafficBytes'],
                    data_limit=created_user.get('trafficLimitBytes'),
                    expire=datetime.fromisoformat(created_user['expireAt'].replace('Z', '+00:00')) if created_user.get('expireAt') else None
                )
            except Exception as e:
                raise

    async def update_subscription_data_limit(self, username: str, data_limit: int) -> PanelProfile:
        if not await self.check_if_user_exists(username):
            return None
        try:
            response = await self.client.get(f"/users?username={username}")
            response.raise_for_status()
            data = response.json()
            user_data = None
            for user in data['response']['users']:
                if user['username'] == username:
                    user_data = user
                    break
            if not user_data:
                raise Exception("User not found in response")
            user_uuid = user_data['uuid']
            current_limit = user_data.get('trafficLimitBytes', 0)

            update_payload = {
                'uuid': user_uuid,
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
                used_traffic=updated_user['usedTrafficBytes'],
                data_limit=updated_user.get('trafficLimitBytes'),
                expire=datetime.fromisoformat(updated_user['expireAt'].replace('Z', '+00:00')) if updated_user.get('expireAt') else None
            )
        except Exception as e:
            raise

    async def reset_subscription_data_limit(self, username):
        if not await self.check_if_user_exists(username):
            return None
        try:
            response = await self.client.get(f"/users?username={username}")
            response.raise_for_status()
            data = response.json()
            user_data = None
            for user in data['response']['users']:
                if user['username'] == username:
                    user_data = user
                    break
            if not user_data:
                raise Exception("User not found in response")
            user_uuid = user_data['uuid']
            reset_response = await self.client.post(f"/users/{user_uuid}/actions/reset-traffic")
            reset_response.raise_for_status()
            reset_data = reset_response.json()
            reset_user = reset_data['response']
            return PanelProfile(
                username=reset_user['username'],
                status=reset_user['status'].lower(),
                subscription_url=reset_user['subscriptionUrl'],
                used_traffic=reset_user['usedTrafficBytes'],
                data_limit=reset_user.get('trafficLimitBytes'),
                expire=datetime.fromisoformat(reset_user['expireAt'].replace('Z', '+00:00')) if reset_user.get('expireAt') else None
            )
        except Exception as e:
            raise
