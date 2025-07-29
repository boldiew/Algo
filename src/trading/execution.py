from .exchange import BaseExchange
from typing import Any
import json


class ExecutionEngine:
    """Handle order submission to an exchange."""

    def __init__(self, api: BaseExchange):
        self.api = api

    async def place_order(self, signal: Any) -> dict:
        resp = await self.api.place_order(signal.symbol, signal.side, signal.quantity)
        with open("orders.log", "a") as f:
            f.write(json.dumps({"symbol": signal.symbol, "side": signal.side, "qty": signal.quantity, "resp": resp}) + "\n")
        return resp
