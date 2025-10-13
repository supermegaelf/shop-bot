from datetime import datetime, timedelta, UTC

import httpx
from pydantic import ValidationError
from remnawave_api import RemnawaveSDK
from remnawave_api.models import UserResponseDto, UpdateUserRequestDto, CreateUserRequestDto

from .panel import Panel
from .models import PanelProfile
from db.methods import get_vpn_user

import glv

class RemnawavePanel(Panel):
    def __init__(self):
        # Create custom client with proxy headers to bypass ProxyCheckMiddleware
        headers = {
            'X-Forwarded-For': '127.0.0.1',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-Host': 'familiartaste.xyz',
            'X-Real-IP': '127.0.0.1',
            'Authorization': f"Bearer {glv.config['REMNAWAVE_TOKEN']}"
        }
        # Add /api to base_url as remnawave API requires it
        api_base_url = f"{glv.config['PANEL_HOST']}/api"
        client = httpx.AsyncClient(headers=headers, base_url=api_base_url, timeout=30.0)
        self.api = RemnawaveSDK(client=client, base_url=api_base_url, token=glv.config['REMNAWAVE_TOKEN'])
        
    async def check_if_user_exists(self, username) -> bool:
        try:
            user = await self.api.users.get_user_by_username(username)
            return True
        except ValidationError as e:
            # ValidationError means API returned data but SDK couldn't parse it
            # This indicates the user EXISTS but there's a schema mismatch
            return True
        except Exception as e:
            # User not found or other error - consider as not existing
            return False
    
    async def get_panel_user(self, tg_id: int) -> PanelProfile:
            result = await get_vpn_user(tg_id)
            res = await self.check_if_user_exists(result.vpn_id)
            if not res:
                return None
            # Use raw HTTP to bypass ValidationError
            try:
                response = await self.api._client.get(f"/users?username={result.vpn_id}")
                response.raise_for_status()
                data = response.json()
                # Extract user from response
                user_data = data['response']['users'][0]
                # Parse directly to PanelProfile
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
            # Get user data using raw HTTP
            try:
                response = await self.api._client.get(f"/users?username={username}")
                response.raise_for_status()
                data = response.json()
                user_data = data['response']['users'][0]

                user_uuid = user_data['uuid']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    # Reset traffic using raw HTTP
                    reset_response = await self.api._client.post(f"/users/{user_uuid}/reset-traffic")
                    reset_response.raise_for_status()
                    new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                else:
                    new_expire_at = user_expire_at + timedelta(days=months*30)

                # Update user using raw HTTP
                update_payload = {
                    'uuid': user_uuid,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': data_limit,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.api._client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                # Return PanelProfile from updated data
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
            # Create new user using raw HTTP
            try:
                new_expire_at = datetime.now(UTC) + timedelta(days=months*30)
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': data_limit,
                    'trafficLimitStrategy': 'MONTH',
                    'activateAllInbounds': True
                }
                create_response = await self.api._client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()

                # Return PanelProfile from created data
                created_user = created_data['response']
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
            # Get user data using raw HTTP to bypass ValidationError
            try:
                response = await self.api._client.get(f"/users?username={username}")
                response.raise_for_status()
                data = response.json()

                # Extract user from response
                user_data = data['response']['users'][0]

                user_uuid = user_data['uuid']
                user_expire_at = datetime.fromisoformat(user_data['expireAt'].replace('Z', '+00:00'))

                if user_expire_at < datetime.now(UTC):
                    new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                else:
                    new_expire_at = user_expire_at + timedelta(hours=glv.config['PERIOD_LIMIT'])

                # Use raw HTTP for update to bypass ValidationError
                update_payload = {
                    'uuid': user_uuid,
                    'status': 'ACTIVE',
                    'trafficLimitBytes': 10737418240,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z')
                }
                update_response = await self.api._client.patch(f"/users", json=update_payload)
                update_response.raise_for_status()
                updated_data = update_response.json()

                # Return PanelProfile from updated data
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
            # Create new user using raw HTTP
            try:
                new_expire_at = datetime.now(UTC) + timedelta(hours=glv.config['PERIOD_LIMIT'])
                create_payload = {
                    'username': username,
                    'expireAt': new_expire_at.isoformat().replace('+00:00', 'Z'),
                    'trafficLimitBytes': 10737418240,
                    'trafficLimitStrategy': 'MONTH',
                    'activateAllInbounds': True
                }
                create_response = await self.api._client.post(f"/users", json=create_payload)
                create_response.raise_for_status()
                created_data = create_response.json()

                # Return PanelProfile from created data
                created_user = created_data['response']
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

        # Get user data using raw HTTP
        try:
            response = await self.api._client.get(f"/users?username={username}")
            response.raise_for_status()
            data = response.json()
            user_data = data['response']['users'][0]

            user_uuid = user_data['uuid']
            current_limit = user_data.get('trafficLimitBytes', 0)

            # Update traffic limit using raw HTTP
            update_payload = {
                'uuid': user_uuid,
                'status': 'ACTIVE',
                'trafficLimitBytes': current_limit + data_limit
            }
            update_response = await self.api._client.patch(f"/users", json=update_payload)
            update_response.raise_for_status()
            updated_data = update_response.json()

            # Return PanelProfile from updated data
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

        # Get user data using raw HTTP
        try:
            response = await self.api._client.get(f"/users?username={username}")
            response.raise_for_status()
            data = response.json()
            user_data = data['response']['users'][0]

            user_uuid = user_data['uuid']

            # Reset traffic using raw HTTP
            reset_response = await self.api._client.post(f"/users/{user_uuid}/reset-traffic")
            reset_response.raise_for_status()
            reset_data = reset_response.json()

            # Return PanelProfile from reset data
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