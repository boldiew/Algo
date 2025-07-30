import asyncio
from typing import Optional
from .base import BaseExchange


class SimulatedExchange(BaseExchange):
    """In-memory exchange used for backtesting and paper trading."""

    def __init__(self):
        self.orders: list[dict] = []

    async def get_ws_token(self) -> str:
        return ""

    async def place_order(
        self, symbol: str, side: str, size: float, price: Optional[float] = None
    ) -> dict:
        order = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "status": "filled",
        }
        self.orders.append(order)
        await asyncio.sleep(0)
        return order
