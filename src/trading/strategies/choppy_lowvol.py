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
    last_move = market_slice.get("last_move", 0)
    side = "LONG" if last_move < 0 else "SHORT"
    return StrategySignal(
        symbol=market_slice.get("symbol", ""),
        strategy_id="Grid-Range",
        side=side,
        quantity=1.0,
        sl_percent=0.01,
        tp_percent=0.015,
        valid_for=60,
    )
