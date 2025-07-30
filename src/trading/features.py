import pandas as pd
import numpy as np
from datetime import datetime
from collections import deque
from scipy.stats import entropy


def hurst_exponent(series: pd.Series) -> float:
    lags = range(2, 20)
    tau = [np.std(series[lag:] - series[:-lag]) + 1e-9 for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return 2 * poly[0]


def return_entropy(series: pd.Series, bins: int = 10) -> float:
    hist, _ = np.histogram(series, bins=bins, density=True)
    return entropy(hist + 1e-8)

class FeatureFabric:
    """Compute derived market features from raw ticks."""

    def __init__(self, vol_window: int = 30):
        self.df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        self.last_ts = None
        self.vol_window = vol_window
        self.surf_windows = [10, 30, 60]
        self.funding_rates: deque[float] = deque(maxlen=200)

    def _funding_z(self, rate: float) -> float:
        self.funding_rates.append(rate)
        arr = np.array(self.funding_rates, dtype=float)
        mean = arr.mean()
        std = arr.std() + 1e-9
        return float((rate - mean) / std)

    def update(self, tick: dict) -> dict:
        ts = pd.to_datetime(tick.get("ts") or tick.get("time"), unit="ms", utc=True)
        price = float(tick.get("price") or tick.get("lastPrice") or tick.get("lastTradePrice") or 0.0)
        size = float(tick.get("size") or 0.0)
        ts_sec = ts.floor("1s")

        if self.last_ts is not None and ts_sec > self.last_ts:
            # forward fill gaps up to 60s
            while self.last_ts + pd.Timedelta(seconds=1) < ts_sec and (ts_sec - self.last_ts).seconds <= 60:
                self.last_ts += pd.Timedelta(seconds=1)
                self.df.loc[self.last_ts] = self.df.iloc[-1]

        if ts_sec not in self.df.index:
            self.df.loc[ts_sec] = [price, price, price, price, size]
        else:
            row = self.df.loc[ts_sec]
            row["high"] = max(row["high"], price)
            row["low"] = min(row["low"], price)
            row["close"] = price
            row["volume"] += size
            self.df.loc[ts_sec] = row

        self.last_ts = ts_sec
        df = self.df.sort_index()
        df["return"] = df["close"].pct_change().fillna(0)
        df["vol"] = df["return"].rolling(self.vol_window, min_periods=1).std().fillna(0)
        df["ma10"] = df["close"].rolling(10, min_periods=1).mean()
        df["ma60"] = df["close"].rolling(60, min_periods=1).mean()
        for w in self.surf_windows:
            df[f"vol_{w}"] = df["return"].rolling(w, min_periods=1).std().fillna(0)
        entropy_val = return_entropy(df["return"].dropna().values[-60:])
        hurst_val = hurst_exponent(df["close"].dropna())
        features = df.iloc[-1].to_dict()
        features["symbol"] = tick.get("symbol", "")
        features["entropy"] = float(entropy_val)
        features["hurst"] = float(hurst_val)
        features["imbalance"] = (
            (float(tick.get("bestBidSize", 0)) - float(tick.get("bestAskSize", 0))) /
            (float(tick.get("bestBidSize", 0)) + float(tick.get("bestAskSize", 1e-9)))
        )
        if len(df) > 1:
            prev = df.iloc[-2]
            for col in ["open", "high", "low", "close", "volume"]:
                features[f"d_{col}"] = df.iloc[-1][col] - prev[col]
        ob_mid = (float(tick.get("bestBidPrice", price)) + float(tick.get("bestAskPrice", price))) / 2
        depth = float(tick.get("bestBidSize", 0)) + float(tick.get("bestAskSize", 0))
        features["depth_mid"] = ob_mid
        features["depth"] = depth
        if "funding_rate" in tick:
            rate = float(tick["funding_rate"])
            features["funding_rate"] = rate
            features["funding_z"] = self._funding_z(rate)
        if "fg_score" in tick:
            features["fg_score"] = float(tick["fg_score"])
        if "social_trend" in tick:
            features["social_trend"] = float(tick["social_trend"])
        return features
