import aiohttp
import base64
import hashlib
import hmac
import time
import json
from typing import Optional
from .base import BaseExchange


class KucoinClient(BaseExchange):
    """Minimal KuCoin REST client for market data token and order placement."""

    def __init__(self, api_key: str, secret: str, passphrase: str, base_url: str = "https://api-futures.kucoin.com"):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.base_url = base_url.rstrip("/")

    def _sign(self, method: str, path: str, body: str = "") -> tuple[str, str]:
        ts = str(int(time.time() * 1000))
        to_sign = ts + method.upper() + path + body
        sign = base64.b64encode(hmac.new(self.secret.encode(), to_sign.encode(), hashlib.sha256).digest()).decode()
        passphrase = base64.b64encode(hmac.new(self.secret.encode(), self.passphrase.encode(), hashlib.sha256).digest()).decode()
        return ts, sign, passphrase

    async def get_ws_token(self) -> str:
        url_path = "/api/v1/bullet-public"
        url = f"{self.base_url}{url_path}"
        ts, sign, passphrase = self._sign("POST", url_path)
        headers = {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": sign,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-TIMESTAMP": ts,
            "KC-API-KEY-VERSION": "2",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                data = await resp.json()
                return data["data"]["token"]

    async def place_order(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> dict:
        path = "/api/v1/orders"
        url = f"{self.base_url}{path}"
        payload = {
            "clientOid": f"codex-{int(time.time()*1000)}",
            "symbol": symbol,
            "side": side.lower(),
            "type": "market" if price is None else "limit",
            "size": size,
        }
        if price is not None:
            payload["price"] = price
        body = json.dumps(payload)
        ts, sign, passphrase = self._sign("POST", path, body)
        headers = {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": sign,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-TIMESTAMP": ts,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=body, headers=headers) as resp:
                return await resp.json()
