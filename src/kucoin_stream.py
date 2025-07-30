import asyncio
import json
import logging
import time
from collections import deque
from typing import AsyncIterator, Dict, List

import aiohttp
import pandas as pd
import websockets

LOGGER = logging.getLogger(__name__)


class UnifiedIndex:
    """Maintain a unified event-time index with gap handling."""

    def __init__(self) -> None:
        self.index = deque()
        self.last_ts: pd.Timestamp | None = None

    def add(self, ts: float) -> pd.Timestamp:
        timestamp = pd.to_datetime(ts, unit="ms")
        if self.last_ts is None:
            self.index.append(timestamp)
            self.last_ts = timestamp
            return timestamp

        delta = (timestamp - self.last_ts).total_seconds()
        if delta > 60:
            self.index.append(pd.NaT)
            self.index.append(timestamp)
        else:
            start = self.last_ts + pd.Timedelta(seconds=1)
            missing = pd.date_range(start, timestamp, freq="s")
            for t in missing[:-1]:
                self.index.append(t)
            self.index.append(timestamp)
        self.last_ts = timestamp
        return timestamp


class KucoinDataStream:
    """Ingests market data from KuCoin Futures."""

    BASE_HTTP = "https://api-futures.kucoin.com"

    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.websocket = None
        self.index = UnifiedIndex()

    async def _get_ws_endpoint(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_HTTP}/api/v1/bullet-public"
            ) as resp:
                data = await resp.json()
        server = data["data"]["instanceServers"][0]
        token = data["data"]["token"]
        return f"{server['endpoint']}?token={token}"  # nosec

    async def connect(self) -> None:
        url = await self._get_ws_endpoint()
        self.websocket = await websockets.connect(url, ping_interval=None)
        await self._subscribe()

    async def _subscribe(self) -> None:
        topics = []
        for symbol in self.symbols:
            topics.extend([
                f"/contractMarket/execution:{symbol}",
                f"/contractMarket/candles:{symbol}_1s",
                f"/contractMarket/candles:{symbol}_5s",
                f"/contractMarket/candles:{symbol}_1min",
                f"/contractMarket/level2:{symbol}",
                f"/contractMarket/fundingRate:{symbol}",
                f"/contractMarket/openInterest:{symbol}",
                f"/contractMarket/LiquidationOrders:{symbol}",
            ])
        msg = {
            "id": int(time.time() * 1000),
            "type": "subscribe",
            "topic": topics,
            "privateChannel": False,
            "response": True,
        }
        await self.websocket.send(json.dumps(msg))

    async def messages(self) -> AsyncIterator[Dict]:
        if self.websocket is None:
            await self.connect()
        async for msg in self.websocket:
            data = json.loads(msg)
            ts = (
                data.get("data", {}).get("time")
                or data.get("data", {}).get("timestamp")
            )
            if ts:
                data["event_time"] = self.index.add(ts)
            yield data


async def _example() -> None:
    stream = KucoinDataStream(["BTCUSDTM"])
    async for message in stream.messages():
        LOGGER.info(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_example())
