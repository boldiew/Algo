from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat_completion

class FundamentalsAgent(BaseAgent):
    name = "Fundamentals"

    def __init__(self):
        super().__init__()

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = f"FundingZ={market_slice.get('funding_z')}, volume={market_slice.get('volume')}. Direction LONG/SHORT/FLAT with confidence."
        try:
            text = await chat_completion(prompt, system="You analyze futures fundamentals")
            direction, conf = text.split()[0], float(text.split()[1])
        except Exception:
            volume = market_slice.get("volume", 0)
            direction = "LONG" if market_slice.get("funding_z",0) < 0 else "SHORT"
            conf = min(1.0, volume/1000)
        res = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction.upper(),
            edge=conf,
            expected_rr=1.0 + conf,
            evidence=[f"llm_conf={conf:.3f}"]
        )
        vec = [market_slice.get("funding_z",0), market_slice.get("volume",0), conf]
        self.memory.add(vec, {"ts": res.ts.isoformat(), "direction": res.direction, "edge": res.edge})
        return res
