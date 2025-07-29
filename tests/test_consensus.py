import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trading.consensus import weighted_consensus
import asyncio
from trading.agents.base import AgentResult


def test_weighted_consensus():
    now = datetime.utcnow()
    results = [
        AgentResult(now, "BTC", "LONG", 0.6, 1.2, ["a"]),
        AgentResult(now, "BTC", "SHORT", 0.4, 0.8, ["b"]),
    ]
    signal = asyncio.run(weighted_consensus([], results, [0.7, 0.3]))
    assert signal.direction == "LONG"
    assert signal.edge > 0.5

def test_direction_disagreement():
    now = datetime.utcnow()
    results = [
        AgentResult(now, "BTC", "LONG", 0.6, 1.2, ["a"]),
        AgentResult(now, "BTC", "SHORT", 0.6, 0.8, ["b"]),
    ]
    signal = asyncio.run(weighted_consensus([], results, [0.5, 0.5]))
    assert signal.direction == "FLAT"
