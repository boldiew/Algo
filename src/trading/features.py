import pandas as pd
from datetime import datetime

class FeatureFabric:
    """Compute derived market features from raw ticks."""

    def __init__(self, vol_window: int = 30):
        self.df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        self.last_ts = None
        self.vol_window = vol_window

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
        features = df.iloc[-1].to_dict()
        features["symbol"] = tick.get("symbol", "")
        features["imbalance"] = (
            (float(tick.get("bestBidSize", 0)) - float(tick.get("bestAskSize", 0))) /
            (float(tick.get("bestBidSize", 0)) + float(tick.get("bestAskSize", 1e-9)))
        )
        return features
