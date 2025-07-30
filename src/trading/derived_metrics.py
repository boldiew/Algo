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

    def _depth_at_pct(self, orderbook: Dict, pct: float) -> tuple[float, float]:
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        if not bids or not asks:
            return 0.0, 0.0
        mid = (bids[0][0] + asks[0][0]) / 2
        th = mid * pct
        bid_d = sum(size for price, size in bids if price >= mid - th)
        ask_d = sum(size for price, size in asks if price <= mid + th)
        return bid_d, ask_d

    def _slippage_cost(self, orderbook: Dict, usd: float) -> float:
        asks = orderbook.get("asks", [])
        if not asks:
            return 0.0
        qty = usd / asks[0][0]
        remain = qty
        cost = 0.0
        for price, size in asks:
            take = min(size, remain)
            cost += take * price
            remain -= take
            if remain <= 0:
                break
        if remain > 0:
            cost += remain * asks[-1][0]
        avg_price = cost / qty
        return (avg_price - asks[0][0]) / asks[0][0]

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
            "Open",
            "High",
            "Low",
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
            "TradeCount",
            "AdverseSelectionCost",
            "LiquidationPressureBuy",
            "LiquidationPressureSell",
            "LiquidationClusterDensity",
        ]
        df = self.tables.setdefault(symbol, pd.DataFrame(columns=base_cols))
        if ts not in df.index:
            prev_num = df["VWAP_numerator"].iloc[-1] if len(df) else 0.0
            prev_vol = df["Volume"].iloc[-1] if len(df) else 0.0
            prev_cvd = df["CVD"].iloc[-1] if len(df) else 0.0
            df.loc[ts, "Open"] = price
            df.loc[ts, "High"] = price
            df.loc[ts, "Low"] = price
            df.loc[ts, "VWAP_numerator"] = prev_num
            df.loc[ts, "Volume"] = prev_vol
            df.loc[ts, "CVD"] = prev_cvd
            df.loc[ts, "TradeCount"] = 0
            df.loc[ts, "AdverseSelectionCost"] = 0.0
            df.loc[ts, "LiquidationPressureBuy"] = 0.0
            df.loc[ts, "LiquidationPressureSell"] = 0.0
            df.loc[ts, "LiquidationClusterDensity"] = 0.0

        df.loc[ts, "LastPrice"] = price
        if ts in df.index:
            df.loc[ts, "High"] = max(df.loc[ts, "High"], price)
            df.loc[ts, "Low"] = min(df.loc[ts, "Low"], price)
        df.loc[ts, "Open"] = df.loc[ts, "Open"] if pd.notna(df.loc[ts, "Open"]) else price
        df.loc[ts, "SpotPrice"] = spot_price
        df.loc[ts, "FundingRate"] = funding_rate
        df.loc[ts, "OpenInterest"] = open_interest
        df.loc[ts, "LongOI"] = long_oi
        df.loc[ts, "ShortOI"] = short_oi
        df.loc[ts, "MarketCap"] = market_cap

        df.loc[ts, "VWAP_numerator"] += price * size
        df.loc[ts, "Volume"] += size
        df.loc[ts, "TradeCount"] += 1
        best_bid = orderbook.get("bids", [[price, 0]])[0][0]
        best_ask = orderbook.get("asks", [[price, 0]])[0][0]
        mp = (
            best_bid * orderbook.get("asks", [[0, 0]])[0][1]
            + best_ask * orderbook.get("bids", [[0, 0]])[0][1]
        ) / (orderbook.get("asks", [[0, 1e-9]])[0][1] + orderbook.get("bids", [[0, 1e-9]])[0][1])
        if side == "buy":
            df.loc[ts, "CVD"] += size
            df.loc[ts, "AdverseSelectionCost"] += (price - mp) * size
        else:
            df.loc[ts, "CVD"] -= size
            df.loc[ts, "AdverseSelectionCost"] += (mp - price) * size

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
        df["PredictedFunding"] = df["FundingRate"].rolling(8).mean()
        df["BasisMomentum_1m"] = df["BasisPremium"].diff(1)
        df["BasisMomentum_5m"] = df["BasisPremium"].diff(5)
        df["BasisMomentum_1h"] = df["BasisPremium"].diff(60)
        df["OIΔ_1m"] = df["OpenInterest"].diff(1)
        df["OIΔ_5m"] = df["OpenInterest"].diff(5)
        df["OIΔ_1h"] = df["OpenInterest"].diff(60)
        df["OpenInterestUSD"] = df["OpenInterest"] * df["LastPrice"]
        df["LeverageRatio"] = df["OpenInterest"] / (df["MarketCap"] + 1e-9)
        df["LongShortRatio"] = df["LongOI"] / (df["ShortOI"] + 1e-9)
        df["NetOIFlow"] = df["LongOI"].diff().fillna(0) - df["ShortOI"].diff().fillna(0)
        df["OrderBookImbalance"] = self._orderbook_imbalance(orderbook)
        df["Return"] = df["LastPrice"].pct_change().fillna(0)
        df["RealizedVolatility_5m"] = df["Return"].rolling(5).std() * np.sqrt(5)
        df["RealizedVolatility_1h"] = df["Return"].rolling(60).std() * np.sqrt(60)
        df["RealizedVolatility_24h"] = df["Return"].rolling(60 * 24).std() * np.sqrt(60 * 24)
        df["VolatilityImpulse"] = df["RealizedVolatility_5m"].diff()
        df["VolOfVol"] = df["RealizedVolatility_5m"].rolling(20).std()
        if "BTCUSDTM" in self.tables and symbol != "BTCUSDTM":
            btc_ret = self.tables["BTCUSDTM"]["Return"].dropna()
            own_ret = df["Return"].dropna()
            r1, r2 = own_ret.align(btc_ret, join="inner")
            if len(r1) >= 2:
                span = 60 * 24 * 60  # 60 days
                cov = np.cov(r1[-span:], r2[-span:])[0, 1]
                var = np.var(r2[-span:]) + 1e-9
                df.loc[ts, "BetaBTC"] = cov / var
        if "BTCUSDTM" in self.tables:
            other_basis = self.tables["BTCUSDTM"]["BasisPremium"].reindex(df.index)
            df["CrossExchangeBasis"] = df["BasisPremium"] - other_basis
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
        df["ZScoreReturns"] = (df["Return"] - df["Return"].rolling(60).mean()) / (
            df["Return"].rolling(60).std() + 1e-9
        )

        ma20 = df["LastPrice"].rolling(20).mean()
        std20 = df["LastPrice"].rolling(20).std()
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        df["BollingerBandwidth"] = (upper - lower) / (ma20 + 1e-9)

        ema20 = df["LastPrice"].ewm(span=20, adjust=False).mean()
        high_low = df["High"] - df["Low"]
        tr1 = high_low
        tr2 = (df["High"] - df["LastPrice"].shift(1)).abs()
        tr3 = (df["Low"] - df["LastPrice"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        df["ATRBandsWidth"] = (2 * atr14) / (df["LastPrice"] + 1e-9)
        df["KeltnerChannelWidth"] = (4 * atr14) / (ema20 + 1e-9)
        depth01 = self._depth_at_pct(orderbook, 0.001)
        depth05 = self._depth_at_pct(orderbook, 0.005)
        mid = (orderbook.get("bids", [[price, 0]])[0][0] + orderbook.get("asks", [[price, 0]])[0][0]) / 2
        spread = orderbook.get("asks", [[price, 0]])[0][0] - orderbook.get("bids", [[price, 0]])[0][0]
        df.loc[ts, "DepthAt0_1pct"] = sum(depth01)
        df.loc[ts, "DepthAt0_5pct"] = sum(depth05)
        df.loc[ts, "LiquiditySlope"] = (df.loc[ts, "DepthAt0_5pct"] - df.loc[ts, "DepthAt0_1pct"]) / (mid * 0.004 + 1e-9)
        df.loc[ts, "BidAskSpread"] = spread
        df.loc[ts, "QuotedSpread"] = spread / (mid + 1e-9)
        df.loc[ts, "MicroPrice"] = (
            orderbook.get("asks", [[price, 0]])[0][0] * orderbook.get("bids", [[0, 0]])[0][1]
            + orderbook.get("bids", [[price, 0]])[0][0] * orderbook.get("asks", [[0, 0]])[0][1]
        ) / (orderbook.get("bids", [[0, 1e-9]])[0][1] + orderbook.get("asks", [[0, 1e-9]])[0][1])
        df.loc[ts, "SlippageCost1kUSD"] = self._slippage_cost(orderbook, 1000)

        df["CumulativeFunding"] = df["FundingRate"].cumsum()
        df["CumulativeFundingAbsolute"] = df["FundingRate"].abs().cumsum()
        df["FundingVolatility"] = df["FundingRate"].rolling(60 * 24).std()
        df["FundingLeverageCompositeIndex"] = df["FundingRate"] * df["LeverageRatio"]

        delta = df["LastPrice"].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        rs = roll_up / (roll_down + 1e-9)
        rsi = 100 - 100 / (1 + rs)
        df["RSI"] = rsi

        min_rsi = rsi.rolling(14).min()
        max_rsi = rsi.rolling(14).max()
        df["StochasticRSI"] = (rsi - min_rsi) / (max_rsi - min_rsi + 1e-9)

        direction = np.sign(delta.fillna(0))
        df["OBV"] = (direction * df["Volume"]).cumsum()

        ema1 = df["LastPrice"].ewm(span=9, adjust=False).mean()
        ema2 = ema1.ewm(span=9, adjust=False).mean()
        ema3 = ema2.ewm(span=9, adjust=False).mean()
        df["TRIX"] = ema3.pct_change() * 100

        mf_mul = ((df["LastPrice"] - df["Low"]) - (df["High"] - df["LastPrice"])) / (df["High"] - df["Low"] + 1e-9)
        mf_vol = mf_mul * df["Volume"]
        df["ChaikinMoneyFlow"] = mf_vol.rolling(20).sum() / df["Volume"].rolling(20).sum().replace(0, np.nan)

        typical_price = (df["High"] + df["Low"] + df["LastPrice"]) / 3
        money_flow = typical_price * df["Volume"]
        pos_mf = money_flow.where(typical_price > typical_price.shift(1), 0.0)
        neg_mf = money_flow.where(typical_price < typical_price.shift(1), 0.0)
        mf_ratio = pos_mf.rolling(14).sum() / (neg_mf.rolling(14).sum().abs() + 1e-9)
        df["MoneyFlowIndex"] = 100 - (100 / (1 + mf_ratio))

        df["TWAP"] = df["LastPrice"].rolling(20).mean()
        df["TWAPDeviation"] = (df["LastPrice"] - df["TWAP"]) / (df["TWAP"] + 1e-9)

        span_10d = 60 * 24 * 10
        span_20d = 60 * 24 * 20
        df["HV10d"] = df["Return"].rolling(span_10d).std() * np.sqrt(span_10d)
        df["HV20d"] = df["Return"].rolling(span_20d).std() * np.sqrt(span_20d)
        wins = df["Return"].rolling(60).apply(lambda x: np.sum(x > 0), raw=True)
        losses = df["Return"].rolling(60).apply(lambda x: np.sum(x < 0), raw=True)
        df["WinLossRatio"] = wins / (losses + 1e-9)
        df["RollingSharpeRatio"] = (
            df["Return"].rolling(60 * 24).mean()
            / (df["Return"].rolling(60 * 24).std() + 1e-9)
        )
        downside = df["Return"].rolling(60 * 24).apply(
            lambda x: np.sqrt(np.mean(np.square(np.minimum(0, x)))), raw=True
        )
        df["RollingSortinoRatio"] = (
            df["Return"].rolling(60 * 24).mean() / (downside + 1e-9)
        )
        drawdown = (df["LastPrice"] / df["LastPrice"].cummax()) - 1
        df["UlcerIndex"] = np.sqrt((drawdown.pow(2)).rolling(14).mean())

        df["AggressorVolumeDelta"] = df["CVD"].diff().fillna(0)
        df["NetAggressorVolumeFlow"] = df["AggressorVolumeDelta"].rolling(5).sum()
        vol_delta = df["Volume"].diff().replace(0, np.nan)
        df["FlowImbalance"] = df["AggressorVolumeDelta"] / vol_delta
        df["MeanTradeSize"] = vol_delta / df["TradeCount"].replace(0, np.nan)
        df["TradeIntensity"] = df["TradeCount"]
        df["LiquidationVolumeBuy"] = df["LiquidationPressureBuy"]
        df["LiquidationVolumeSell"] = df["LiquidationPressureSell"]
        df["PendingLiquidationPressure"] = df["LiquidationPressureBuy"].diff().fillna(0) - df["LiquidationPressureSell"].diff().fillna(0)
        df["LiquidityStressIndex"] = (
            df["QuotedSpread"].rolling(5).mean()
            / (df["DepthAt0_5pct"].rolling(5).mean() + 1e-9)
        )

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
