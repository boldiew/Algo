import aiohttp
from typing import Optional
from .base import BaseExchange


class KucoinClient(BaseExchange):
    """Minimal KuCoin REST client for market data token and order placement."""

    def __init__(self, api_key: str, secret: str, passphrase: str, base_url: str = "https://api-futures.kucoin.com"):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.base_url = base_url.rstrip("/")

    async def get_ws_token(self) -> str:
        url = f"{self.base_url}/api/v1/bullet-public"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                data = await resp.json()
                return data["data"]["token"]

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
        headers = {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": "stub",
            "KC-API-PASSPHRASE": self.passphrase,
            "KC-API-TIMESTAMP": "0",
            "KC-API-KEY-VERSION": "2",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                return await resp.json()
