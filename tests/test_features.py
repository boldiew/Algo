import numpy as np
import pandas as pd
from trading.features import hurst_exponent, FeatureFabric
from datetime import datetime, timedelta


def test_hurst_range():
    data = pd.Series(np.cumsum(np.random.randn(500)))
    h = hurst_exponent(data)
    assert 0 <= h <= 2


def test_feature_keys():
    fab = FeatureFabric()
    ts = int(datetime.utcnow().timestamp() * 1000)
    tick1 = {
        "ts": ts,
        "price": 100.0,
        "size": 1.0,
        "bestBidSize": 5.0,
        "bestAskSize": 4.0,
        "bestBidPrice": 99.0,
        "bestAskPrice": 101.0,
    }
    tick2 = {
        "ts": ts + 1000,
        "price": 101.0,
        "size": 1.0,
        "bestBidSize": 4.0,
        "bestAskSize": 5.0,
        "bestBidPrice": 100.0,
        "bestAskPrice": 102.0,
    }
    fab.update(tick1)
    features = fab.update(tick2)
    for key in ["trend_strength", "volatility_state", "order_flow_bias", "last_move"]:
        assert key in features
