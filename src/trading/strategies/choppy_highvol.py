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
    bias = market_slice.get("order_flow_bias", 0)
    side = "LONG" if bias > 0 else "SHORT"
    return StrategySignal(
        symbol=market_slice.get("symbol", ""),
        strategy_id="VWAP-MeanRev",
        side=side,
        quantity=1.0,
        sl_percent=0.012,
        tp_percent=0.025,
        valid_for=60,
    )
