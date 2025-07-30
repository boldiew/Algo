import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trading.state import StateStore


def test_store_and_load_trades(tmp_path):
    path = tmp_path / "state.json"
    store = StateStore(str(path))
    store.store_open_trades([{"symbol": "BTC", "qty": 1}])
    store.store_trade_log([{"ts": datetime.utcnow().isoformat(), "symbol": "BTC"}])
    store.save()
    new_store = StateStore(str(path))
    assert new_store.load_open_trades()[0]["symbol"] == "BTC"
    assert new_store.load_trade_log()
