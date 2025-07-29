import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trading.risk import RiskEngine


def test_risk_engine_limits():
    r = RiskEngine({"daily_stop": -0.02, "intraday_stop": -0.03, "equity": 1.0})
    r.update(-0.015)
    assert r.allows_trade("BTC", 0.1)
    r.update(-0.01)
    assert not r.allows_trade("BTC", 0.1)
