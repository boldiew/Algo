import aiohttp
from typing import Optional
import json
import hmac
import hashlib
import base64
import time
from .base import BaseExchange


class KucoinClient(BaseExchange):
    """Minimal KuCoin REST client for market data token and order placement."""

    def __init__(self, api_key: str, secret: str, passphrase: str, base_url: str = "https://api-futures.kucoin.com"):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.base_url = base_url.rstrip("/")

    async def get_ws_token(self) -> str:
        """Retrieve websocket token for public market streams."""
        url = f"{self.base_url}/api/v1/bullet-public"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as resp:
                    data = await resp.json()
                    return data["data"]["token"]
        except aiohttp.ClientError as exc:
            raise ConnectionError(f"Failed to obtain KuCoin token: {exc}") from exc

    async def place_order(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> dict:
        url = f"{self.base_url}/api/v1/orders"
        payload = {
            "clientOid": "codex-order",
            "symbol": symbol,
            "side": side.lower(),
            "type": "market" if price is None else "limit",
            "size": size,
        }
        if price is not None:
            payload["price"] = price
        timestamp = str(int(time.time() * 1000))
        str_to_sign = timestamp + 'POST' + '/api/v1/orders' + json.dumps(payload)
        signature = base64.b64encode(hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode()
        passphrase = base64.b64encode(hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest()).decode()
        headers = {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-KEY-VERSION": "2",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                return await resp.json()
