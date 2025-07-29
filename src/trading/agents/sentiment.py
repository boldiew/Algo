from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict

class SentimentAgent(BaseAgent):
    name = "Sentiment"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        ret = market_slice.get("return", 0.0)
        direction = "LONG" if ret > 0 else "SHORT" if ret < 0 else "FLAT"
        edge = min(1.0, abs(ret) * 10)
        return AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[f"return={ret:.5f}"]
        )
