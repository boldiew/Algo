import abc


class BaseExchange(abc.ABC):
    """Abstract exchange interface"""

    @abc.abstractmethod
    async def get_ws_token(self) -> str:
        """Return websocket token for market streams"""

    @abc.abstractmethod
    async def place_order(self, symbol: str, side: str, size: float, price: float | None = None) -> dict:
        """Place an order and return exchange response"""
