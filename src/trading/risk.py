class RiskEngine:
    def __init__(self, config: dict):
        self.daily_stop = config.get("daily_stop", -0.02)
        self.intraday_stop = config.get("intraday_stop", -0.03)
        self.equity = config.get("equity", 1.0)
        self.max_pair_exposure = config.get("max_pair_exposure", 1.0)
        self.max_corr_exposure = config.get("max_corr_exposure", 1.5)
        self.liquidation_buffer = config.get("liquidation_buffer", 0.1)
        self.day_pnl = 0.0
        self.intraday_pnl = 0.0
        self.exposures: dict[str, float] = {}

    def update(self, pnl: float):
        self.day_pnl += pnl
        self.intraday_pnl += pnl

    def allows_trade(self, symbol: str, qty: float) -> bool:
        if self.day_pnl <= self.daily_stop * self.equity:
            return False
        if self.intraday_pnl <= self.intraday_stop * self.equity:
            return False
        if abs(self.exposures.get(symbol, 0) + qty) > self.max_pair_exposure * self.equity:
            return False
        total = sum(abs(v) for v in self.exposures.values()) + abs(qty)
        if total > self.max_corr_exposure * self.equity:
            return False
        if self.equity - total < self.liquidation_buffer * self.equity:
            return False
        return True

    def record_fill(self, symbol: str, qty: float, pnl: float):
        self.update(pnl)
        self.exposures[symbol] = self.exposures.get(symbol, 0.0) + qty

    def reset_intraday(self):
        self.intraday_pnl = 0.0
