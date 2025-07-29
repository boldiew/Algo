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
    momentum = market_slice.get("trend_strength", 0)
    side = "LONG" if momentum > 0 else "SHORT"
    return StrategySignal(
        symbol=market_slice.get("symbol", ""),
        strategy_id="Pullback-EMA",
        side=side,
        quantity=1.0,
        sl_percent=0.008,
        tp_percent=0.015,
        valid_for=60,
    )
