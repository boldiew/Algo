import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from config import Config
from execution_engine import ExecutionEngine


def test_backtest_execute():
    cfg = Config()
    cfg.mode = 'backtest'
    engine = ExecutionEngine(cfg)
    order = {'symbol': 'BTC-USDT', 'side': 'buy', 'size': 1, 'price': 10000}
    result = engine.execute(order)
    assert result['filled'] is True
