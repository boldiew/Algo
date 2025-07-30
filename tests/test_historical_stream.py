import sys, os, asyncio
sys.path.insert(0, os.path.abspath("src"))
from trading.ingestion import HistoricalDataStream


def test_historical_stream(tmp_path):
    csv = tmp_path / "ticks.csv"
    csv.write_text(
        "ts,price,size,bestBidPrice,bestBidSize,bestAskPrice,bestAskSize\n"
        "1,100,1,99,1,101,1\n"
        "2,101,1,100,1,102,1\n"
    )
    stream = HistoricalDataStream(str(csv))
    async def _collect():
        gen = stream.stream()
        return [await gen.__anext__(), await gen.__anext__()]
    rows = asyncio.run(_collect())
    assert rows[0]["close"] == 100
    assert rows[1]["close"] == 101
