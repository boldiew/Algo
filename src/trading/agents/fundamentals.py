from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict

class FundamentalsAgent(BaseAgent):
    name = "Fundamentals"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        volume = market_slice.get("volume", 0)
        ret = market_slice.get("return", 0)
        direction = "LONG" if ret > 0 else "SHORT" if ret < 0 else "FLAT"
        edge = min(1.0, volume / 1000)
        return AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[f"vol={volume}"]
        )
