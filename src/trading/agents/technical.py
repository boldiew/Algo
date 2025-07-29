from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict

class TechnicalAgent(BaseAgent):
    name = "Technical"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        ma10 = market_slice.get("ma10", market_slice.get("close", 0))
        ma60 = market_slice.get("ma60", market_slice.get("close", 0))
        diff = ma10 - ma60
        price = market_slice.get("close", 0)
        direction = "LONG" if diff > 0 else "SHORT" if diff < 0 else "FLAT"
        edge = min(1.0, abs(diff) / price) if price else 0.5
        return AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[f"ma_diff={diff:.4f}"]
        )
