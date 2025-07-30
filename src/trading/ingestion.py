import asyncio
import json
import websockets
from typing import AsyncIterator, List
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
                features = self.features.update(data["data"])
                yield features
