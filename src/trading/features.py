import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import entropy

def hurst(ts: pd.Series) -> float:
    if len(ts) < 20:
        return 0.0
    lags = range(2, 20)
    tau = [np.sqrt(np.std(ts.diff(lag))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]*2.0

class FeatureFabric:
    """Compute derived market features from raw ticks."""

    def __init__(self, vol_window: int = 30):
        self.df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        self.last_ts = None
        self.vol_window = vol_window
        self.median_vol = 0.0

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
        df["rv5"] = df["return"].rolling(5, min_periods=1).std().fillna(0)
        df["rv15"] = df["return"].rolling(15, min_periods=1).std().fillna(0)
        df["rv30"] = df["return"].rolling(30, min_periods=1).std().fillna(0)
        df["entropy30"] = df["return"].rolling(30, min_periods=1).apply(lambda x: entropy(np.histogram(x, bins=10)[0] + 1e-9), raw=False).fillna(0)
        df["hurst"] = df["close"].rolling(100, min_periods=20).apply(hurst, raw=False).fillna(0)
        if len(df) >= 15:
            highs = df["high"].rolling(14).max()
            lows = df["low"].rolling(14).min()
            close = df["close"]
            tr = (df[["high", "low", "close"]].diff().abs().max(axis=1)).rolling(14).sum()
            up = (highs - highs.shift(1)).clip(lower=0).rolling(14).sum()
            down = (lows.shift(1) - lows).clip(lower=0).rolling(14).sum()
            di_plus = 100 * up / tr
            di_minus = 100 * down / tr
            dx = (abs(di_plus - di_minus) / (di_plus + di_minus + 1e-9)) * 100
            df["adx"] = dx.rolling(14).mean()
        else:
            df["adx"] = 0
        x = np.arange(len(df))
        if len(df) > 1:
            coef = np.polyfit(x, df["close"], 1)
            fitted = np.polyval(coef, x)
            ss_res = ((df["close"] - fitted) ** 2).sum()
            ss_tot = ((df["close"] - df["close"].mean()) ** 2).sum()
            r2 = 1 - ss_res / (ss_tot + 1e-9)
        else:
            r2 = 0
        self.median_vol = df["rv30"].median()
        features = df.iloc[-1].to_dict()
        features["adx"] = df["adx"].iloc[-1]
        features["r2"] = r2
        features["median_vol"] = self.median_vol
        features["symbol"] = tick.get("symbol", "")
        bid = float(tick.get("bestBidPrice", 0))
        ask = float(tick.get("bestAskPrice", 0))
        bid_sz = float(tick.get("bestBidSize", 0))
        ask_sz = float(tick.get("bestAskSize", 0))
        features["imbalance"] = (bid_sz - ask_sz) / (bid_sz + ask_sz + 1e-9)
        features["mid_price"] = (bid + ask) / 2
        features["depth_mid"] = (bid * ask_sz + ask * bid_sz) / (bid_sz + ask_sz + 1e-9)
        features["spread_depth"] = (ask - bid) * (bid_sz + ask_sz)
        funding = float(tick.get("fundingRate", 0))
        df["funding"] = df.get("funding", 0)
        df.loc[ts_sec, "funding"] = funding
        features["funding_z"] = (df["funding"].iloc[-1] - df["funding"].rolling(100, min_periods=1).mean().iloc[-1]) / (df["funding"].rolling(100, min_periods=1).std().iloc[-1] + 1e-9)
        features["return_entropy"] = df["entropy30"].iloc[-1]
        return features
