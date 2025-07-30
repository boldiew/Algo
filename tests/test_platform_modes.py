import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trading.platform import TradingPlatform
from trading.config import Config
from trading.exchange import SimulatedExchange
from trading.ingestion import HistoricalDataStream, KucoinDataStream


def test_backtest_mode(tmp_path, monkeypatch):
    data = (
        "ts,price,size,bestBidSize,bestAskSize,bestBidPrice,bestAskPrice,symbol\n"
        "1630000000000,10000,1,1,1,9999,10001,BTC-USDT\n"
        "1630000001000,10010,1,1,1,10009,10011,BTC-USDT\n"
    )
    csv = tmp_path / "history.csv"
    csv.write_text(data)
    cfg = Config(mode="backtest", risk={}, pairs=["BTC-USDT"], kucoin={}, backtest_path=str(csv))
    monkeypatch.chdir(tmp_path)
    platform = TradingPlatform(cfg)
    assert isinstance(platform.stream, HistoricalDataStream)
    assert isinstance(platform.execution.api, SimulatedExchange)
    first = asyncio.run(platform.stream.stream().__anext__())
    assert "close" in first


def test_paper_mode(tmp_path, monkeypatch):
    cfg = Config(mode="paper", risk={}, pairs=["BTC-USDT"], kucoin={"api_key":"","secret":"","passphrase":""})
    monkeypatch.chdir(tmp_path)
    platform = TradingPlatform(cfg)
    assert isinstance(platform.stream, KucoinDataStream)
    assert isinstance(platform.execution.api, SimulatedExchange)
