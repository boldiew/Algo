import asyncio
import json
import websockets
from typing import AsyncIterator, List
from datetime import datetime, timedelta
import aiohttp
from .exchange import KucoinClient
from .features import FeatureFabric

KUCOIN_WS = "wss://ws-api-futures.kucoin.com/?token={token}"


class KucoinDataStream:
    """Stream ticker data for a list of symbols from KuCoin futures."""

    def __init__(self, client: KucoinClient, symbols: List[str]):
        self.client = client
        self.symbols = symbols
        self.ws = None
        self._token = None
        self.features = FeatureFabric()
        self._sentiment = {"fg_score": 0.5, "social_trend": 0.0}
        self._sentiment_ts = datetime.utcnow() - timedelta(minutes=15)

    async def _update_sentiment(self):
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get("https://api.alternative.me/fng/")
                data = await resp.json()
                val = float(data["data"][0]["value"])
                self._sentiment["fg_score"] = val / 100.0
                resp = await session.get("https://api.coingecko.com/api/v3/search/trending")
                data = await resp.json()
                coins = [c["item"]["symbol"].upper() for c in data.get("coins", [])]
                base = self.symbols[0].split("-")[0].upper()
                self._sentiment["social_trend"] = 1.0 if base in coins else 0.0
        except Exception:
            pass

    async def _get_funding(self, symbol: str) -> float:
        try:
            data = await self.client.get_funding_rate(symbol)
            return float(data)
        except Exception:
            return 0.0

    async def _ensure_token(self):
        if self._token is None:
            self._token = await self.client.get_ws_token()

    async def connect(self):
        await self._ensure_token()
        self.ws = await websockets.connect(KUCOIN_WS.format(token=self._token))

    async def subscribe(self):
        sub = {
            "id": 1,
            "type": "subscribe",
            "topic": f"/contractMarket/tickerV2:{','.join(self.symbols)}",
            "response": True,
        }
        await self.ws.send(json.dumps(sub))

    async def stream(self) -> AsyncIterator[dict]:
        if self.ws is None:
            await self.connect()
            await self.subscribe()
        async for msg in self.ws:
            data = json.loads(msg)
            if data.get("type") == "message":
                tick = data["data"]
                funding = await self._get_funding(tick.get("symbol", ""))
                tick["funding_rate"] = funding
                now = datetime.utcnow()
                if now - self._sentiment_ts > timedelta(minutes=10):
                    await self._update_sentiment()
                    self._sentiment_ts = now
                tick.update(self._sentiment)
                features = self.features.update(tick)
                yield features
