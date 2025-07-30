from .exchange import BaseExchange
from typing import Any


class ExecutionEngine:
    """Handle order submission to an exchange."""

    def __init__(self, api: BaseExchange):
        self.api = api

    async def place_order(self, signal: Any) -> dict:
        return await self.api.place_order(signal.symbol, signal.side, signal.quantity)
