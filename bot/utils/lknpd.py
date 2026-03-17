import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_DEVICE_INFO = {
    "sourceType": "WEB",
    "sourceDeviceId": uuid.uuid4().hex[:21],
    "appVersion": "1.0.0",
    "metaDetails": {
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/88.0.4324.192 Safari/537.36"
        )
    },
}

_API_URL = "https://lknpd.nalog.ru/api"


class LknpdAuthError(Exception):
    pass


class LknpdApiError(Exception):
    pass


class LknpdClient:
    def __init__(self, inn: str, password: str) -> None:
        self._inn = inn
        self._password = password
        self._token_data: dict = {}
        self._refresh_lock = asyncio.Lock()
        self._http = httpx.AsyncClient(timeout=30.0)

    @property
    def _token(self) -> Optional[str]:
        return self._token_data.get("token")

    @property
    def _refresh_token(self) -> Optional[str]:
        return self._token_data.get("refreshToken")

    def _auth_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self._token}",
        }

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise LknpdAuthError(f"401 Unauthorized: {response.text}")
        if response.status_code >= 400:
            raise LknpdApiError(f"{response.status_code}: {response.text}")

    async def authenticate(self) -> None:
        response = await self._http.post(
            f"{_API_URL}/v1/auth/lkfl",
            json={
                "username": self._inn,
                "password": self._password,
                "deviceInfo": _DEVICE_INFO,
            },
            headers={"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"},
        )
        if response.status_code == 401:
            raise LknpdAuthError(f"Authentication failed: {response.text}")
        if response.status_code >= 400:
            raise LknpdApiError(f"{response.status_code}: {response.text}")
        self._token_data = response.json()

    async def _refresh(self) -> None:
        async with self._refresh_lock:
            response = await self._http.post(
                f"{_API_URL}/v1/auth/token",
                json={"refreshToken": self._refresh_token, "deviceInfo": _DEVICE_INFO},
                headers={"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"},
            )
            if response.status_code == 401:
                raise LknpdAuthError(f"Token refresh failed: {response.text}")
            if response.status_code >= 400:
                raise LknpdApiError(f"{response.status_code}: {response.text}")
            self._token_data = response.json()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        response = await self._http.request(
            method, f"{_API_URL}{path}", headers=self._auth_headers(), **kwargs
        )
        if response.status_code == 401:
            await self._refresh()
            response = await self._http.request(
                method, f"{_API_URL}{path}", headers=self._auth_headers(), **kwargs
            )
        self._raise_for_status(response)
        return response.json()

    async def register_income(self, item_name: str, amount: float) -> Optional[str]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        amount_str = f"{amount:.2f}"
        data = await self._request(
            "POST",
            "/v1/income",
            json={
                "operationTime": now,
                "requestTime": now,
                "services": [{"name": item_name, "amount": amount_str, "quantity": 1}],
                "totalAmount": amount_str,
                "client": {
                    "contactPhone": None,
                    "displayName": None,
                    "incomeType": "FROM_INDIVIDUAL",
                    "inn": None,
                },
                "paymentType": "WIRE",
                "ignoreMaxTotalIncomeRestriction": False,
            },
        )
        return (
            data.get("approvedReceiptUuid")
            or data.get("receiptUuid")
            or data.get("receipt_uuid")
        )

    async def aclose(self) -> None:
        await self._http.aclose()


class LknpdService:
    def __init__(self, inn: Optional[str], password: Optional[str]) -> None:
        self.configured = bool(inn and password)
        self._client: Optional[LknpdClient] = None
        self._auth_lock = asyncio.Lock()
        self._authenticated = False

        if self.configured:
            self._client = LknpdClient(inn, password)
        else:
            logger.warning("LKNPD service is not configured: NALOGO_INN or NALOGO_PASSWORD is missing")

    async def _ensure_authenticated(self) -> None:
        async with self._auth_lock:
            if not self._authenticated:
                await self._client.authenticate()
                self._authenticated = True

    async def create_income_receipt(self, *, item_name: str, amount: float) -> Optional[str]:
        if not self.configured:
            return None
        try:
            await self._ensure_authenticated()
            receipt_uuid = await self._client.register_income(item_name=item_name, amount=amount)
            logger.info(f"LKNPD income registered, receipt_uuid={receipt_uuid}")
            return receipt_uuid
        except Exception as exc:
            logger.error(f"LKNPD income registration failed: {exc}")
            return None

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
