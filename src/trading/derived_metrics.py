import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Any


class DerivedMetrics:
    """Compute high level analytics from futures market data."""

    def __init__(self, store_path: str = "metrics.h5"):
        self.store_path = store_path
        self.tables: Dict[str, pd.DataFrame] = {}
        self.subscribers: List[Callable[[str, pd.Series], Any]] = []
        self.master = pd.DataFrame()

    def subscribe(self, callback: Callable[[str, pd.Series], Any]) -> None:
        self.subscribers.append(callback)

    def _persist(self, symbol: str) -> None:
        df = self.tables[symbol]
        try:
            df.to_hdf(self.store_path, key=symbol, mode="a")
        except Exception as exc:  # pragma: no cover - IO errors shouldn't crash
            print(f"Persist failed for {symbol}: {exc}")

    def _broadcast(self, symbol: str, row: pd.Series) -> None:
        for cb in self.subscribers:
            cb(symbol, row)

    def _orderbook_imbalance(self, orderbook: Dict, pct: float = 0.01) -> float:
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        if not bids or not asks:
            return 0.0
        mid = (bids[0][0] + asks[0][0]) / 2
        threshold = mid * pct
        bid_depth = sum(size for price, size in bids if price >= mid - threshold)
        ask_depth = sum(size for price, size in asks if price <= mid + threshold)
        total = bid_depth + ask_depth
        if total == 0:
            return 0.0
        return (bid_depth - ask_depth) / total

    def _max_adverse_excursion(self, returns: pd.Series) -> float:
        cum = (1 + returns).cumprod()
        cum_max = cum.cummax()
        drawdown = (cum - cum_max) / cum_max
        return float(drawdown.min())

    def update(
        self,
        raw_tick: Dict,
        orderbook: Dict,
        funding: Dict,
        oi: Dict,
        liquidations: List[Dict],
    ) -> pd.DataFrame:
        """Update metrics using a new tick and return the full master table."""
        symbol = raw_tick.get("symbol")
        ts = pd.to_datetime(raw_tick.get("ts") or raw_tick.get("time"), unit="ms", utc=True).floor("1min")
        price = float(raw_tick.get("price") or raw_tick.get("lastPrice") or 0.0)
        size = float(raw_tick.get("size") or 0.0)
        side = str(raw_tick.get("side", "buy")).lower()
        spot_price = float(orderbook.get("spot_price", price))
        funding_rate = float(funding.get("fundingRate", 0.0))
        open_interest = float(oi.get("openInterest", 0.0))
        long_oi = float(oi.get("longQty", oi.get("longValue", 0.0)))
        short_oi = float(oi.get("shortQty", oi.get("shortValue", 0.0)))
        market_cap = float(oi.get("marketCap", 0.0))

        base_cols = [
            "LastPrice",
            "SpotPrice",
            "FundingRate",
            "OpenInterest",
            "LongOI",
            "ShortOI",
            "MarketCap",
            "VWAP_numerator",
            "Volume",
            "CVD",
            "LiquidationPressureBuy",
            "LiquidationPressureSell",
            "LiquidationClusterDensity",
        ]
        df = self.tables.setdefault(symbol, pd.DataFrame(columns=base_cols))
        if ts not in df.index:
            prev_num = df["VWAP_numerator"].iloc[-1] if len(df) else 0.0
            prev_vol = df["Volume"].iloc[-1] if len(df) else 0.0
            prev_cvd = df["CVD"].iloc[-1] if len(df) else 0.0
            df.loc[ts, "VWAP_numerator"] = prev_num
            df.loc[ts, "Volume"] = prev_vol
            df.loc[ts, "CVD"] = prev_cvd
            df.loc[ts, "LiquidationPressureBuy"] = 0.0
            df.loc[ts, "LiquidationPressureSell"] = 0.0
            df.loc[ts, "LiquidationClusterDensity"] = 0.0

        df.loc[ts, "LastPrice"] = price
        df.loc[ts, "SpotPrice"] = spot_price
        df.loc[ts, "FundingRate"] = funding_rate
        df.loc[ts, "OpenInterest"] = open_interest
        df.loc[ts, "LongOI"] = long_oi
        df.loc[ts, "ShortOI"] = short_oi
        df.loc[ts, "MarketCap"] = market_cap

        df.loc[ts, "VWAP_numerator"] += price * size
        df.loc[ts, "Volume"] += size
        if side == "buy":
            df.loc[ts, "CVD"] += size
        else:
            df.loc[ts, "CVD"] -= size

        liq_buy = sum(l.get("size", 0.0) for l in liquidations if str(l.get("side", "")).lower() == "buy")
        liq_sell = sum(l.get("size", 0.0) for l in liquidations if str(l.get("side", "")).lower() == "sell")
        prices = [l.get("price", price) for l in liquidations]
        if prices:
            density = len(prices) / (max(prices) - min(prices) + 1e-9)
        else:
            density = 0.0
        df.loc[ts, "LiquidationPressureBuy"] += liq_buy
        df.loc[ts, "LiquidationPressureSell"] += liq_sell
        df.loc[ts, "LiquidationClusterDensity"] = density

        df.sort_index(inplace=True)
        df["VWAP"] = df["VWAP_numerator"] / df["Volume"].replace(0, np.nan)
        df["VWAPDeviation"] = (df["LastPrice"] - df["VWAP"]) / df["VWAP"]
        df["BasisPremium"] = (df["LastPrice"] - df["SpotPrice"]) / df["SpotPrice"]
        df["FundingRateΔ_1h"] = df["FundingRate"].diff(60)
        df["FundingRateΔ_24h"] = df["FundingRate"].diff(60 * 24)
        df["AnnualizedFunding"] = df["FundingRate"] * 3 * 365
        df["BasisMomentum_5m"] = df["BasisPremium"].diff(5)
        df["BasisMomentum_1h"] = df["BasisPremium"].diff(60)
        df["OIΔ_1m"] = df["OpenInterest"].diff(1)
        df["OIΔ_5m"] = df["OpenInterest"].diff(5)
        df["OIΔ_1h"] = df["OpenInterest"].diff(60)
        df["LeverageRatio"] = df["OpenInterest"] / (df["MarketCap"] + 1e-9)
        df["LongShortRatio"] = df["LongOI"] / (df["ShortOI"] + 1e-9)
        df["NetOIFlow"] = df["LongOI"].diff().fillna(0) - df["ShortOI"].diff().fillna(0)
        df["OrderBookImbalance"] = self._orderbook_imbalance(orderbook)
        df["Return"] = df["LastPrice"].pct_change().fillna(0)
        df["RealizedVolatility_5m"] = df["Return"].rolling(5).std() * np.sqrt(5)
        df["RealizedVolatility_1h"] = df["Return"].rolling(60).std() * np.sqrt(60)
        df["RealizedVolatility_24h"] = df["Return"].rolling(60 * 24).std() * np.sqrt(60 * 24)
        if "BTCUSDTM" in self.tables and symbol != "BTCUSDTM":
            btc_ret = self.tables["BTCUSDTM"]["Return"].dropna()
            own_ret = df["Return"].dropna()
            r1, r2 = own_ret.align(btc_ret, join="inner")
            if len(r1) >= 2:
                span = 60 * 24 * 60  # 60 days
                cov = np.cov(r1[-span:], r2[-span:])[0, 1]
                var = np.var(r2[-span:]) + 1e-9
                df.loc[ts, "BetaBTC"] = cov / var
        elif symbol == "BTCUSDTM":
            df.loc[ts, "BetaBTC"] = 1.0
        var_window = df["Return"].rolling(60 * 24)
        df["ValueAtRisk_95"] = var_window.quantile(0.05)
        df["ExpectedShortfall_95"] = var_window.apply(lambda x: x[x <= x.quantile(0.05)].mean(), raw=False)
        df["MaxAdverseExcursion"] = var_window.apply(self._max_adverse_excursion)
        mean_r = var_window.mean()
        var_r = var_window.var() + 1e-9
        df["KellyFraction"] = mean_r / var_r
        sharpe_24h = (df["Return"].rolling(60 * 24).mean()) / (df["Return"].rolling(60 * 24).std() + 1e-9)
        momentum = np.sign(df["Return"].rolling(60).sum())
        df["MomentumScore"] = sharpe_24h * momentum

        self.tables[symbol] = df
        self._persist(symbol)
        self._broadcast(symbol, df.loc[ts])
        self.master = self._assemble_master()
        return self.master

    def _assemble_master(self) -> pd.DataFrame:
        frames = []
        for sym, df in self.tables.items():
            temp = df.copy()
            temp["symbol"] = sym
            frames.append(temp)
        if not frames:
            return pd.DataFrame()
        all_df = pd.concat(frames)
        return all_df.set_index("symbol", append=True).swaplevel(0, 1).sort_index()
