import sys, os
sys.path.insert(0, os.path.abspath("src"))
from trading.derived_metrics import DerivedMetrics
from datetime import datetime


def test_basic_metrics():
    dm = DerivedMetrics(store_path="test_metrics.h5")
    ts = int(datetime.utcnow().timestamp() * 1000)

    raw1 = {"ts": ts, "symbol": "BTCUSDTM", "price": 100.0, "size": 2.0, "side": "buy"}
    ob1 = {"bids": [[99.5, 5.0]], "asks": [[100.5, 5.0]], "spot_price": 100.0}
    fund1 = {"fundingRate": 0.0001}
    oi1 = {"openInterest": 1000, "longQty": 600, "shortQty": 400, "marketCap": 10000}
    dm.update(raw1, ob1, fund1, oi1, [])

    raw2 = {"ts": ts + 60000, "symbol": "BTCUSDTM", "price": 102.0, "size": 2.0, "side": "buy"}
    ob2 = {"bids": [[101.5, 5.0]], "asks": [[102.5, 5.0]], "spot_price": 101.0}
    fund2 = {"fundingRate": 0.0002}
    oi2 = {"openInterest": 1200, "longQty": 700, "shortQty": 500, "marketCap": 10000}
    df = dm.update(raw2, ob2, fund2, oi2, [])

    last = df.loc["BTCUSDTM"].iloc[-1]
    assert abs(last.VWAP - 101.0) < 1e-6
    assert abs(last.AnnualizedFunding - 0.0002 * 3 * 365) < 1e-9
    assert "MomentumScore" in df.columns
    for key in ["RSI", "BollingerBandwidth", "ChaikinMoneyFlow", "AggressorVolumeDelta", "DepthAt0_1pct", "BidAskSpread", "TWAPDeviation"]:
        assert key in df.columns
