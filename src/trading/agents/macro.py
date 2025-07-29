from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict

class MacroAgent(BaseAgent):
    name = "Macro"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        vol = market_slice.get("vol", 0)
        direction = "LONG" if vol < 0.01 else "SHORT"
        edge = min(1.0, abs(0.01 - vol) * 100)
        return AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[f"vol={vol:.5f}"]
        )
