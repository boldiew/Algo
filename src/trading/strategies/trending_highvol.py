from dataclasses import dataclass

@dataclass
class StrategySignal:
    symbol: str
    strategy_id: str
    side: str
    quantity: float
    sl_percent: float
    tp_percent: float
    valid_for: int


def generate_signal(market_slice) -> StrategySignal:
    trend = market_slice.get("trend_strength", 0)
    side = "LONG" if trend > 0 else "SHORT"
    return StrategySignal(
        symbol=market_slice.get("symbol", ""),
        strategy_id="MOM-ATR-Break",
        side=side,
        quantity=1.0,
        sl_percent=0.01,
        tp_percent=0.02,
        valid_for=60,
    )
