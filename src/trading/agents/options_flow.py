from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict

class OptionsFlowAgent(BaseAgent):
    name = "OptionsFlow"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        imb = market_slice.get("imbalance", 0)
        direction = "LONG" if imb > 0 else "SHORT" if imb < 0 else "FLAT"
        edge = min(1.0, abs(imb))
        return AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[f"imbalance={imb:.4f}"]
        )
