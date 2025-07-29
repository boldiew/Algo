from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat_completion

class TechnicalAgent(BaseAgent):
    name = "Technical"

    def __init__(self):
        super().__init__()

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = f"Technical factors: MA10={market_slice.get('ma10')}, MA60={market_slice.get('ma60')}, ADX={market_slice.get('adx')}. Provide LONG/SHORT/FLAT and confidence." 
        try:
            text = await chat_completion(prompt, system="You are a technical trading analyst")
            direction, conf = text.split()[0], float(text.split()[1])
        except Exception:
            ma10 = market_slice.get("ma10", 0)
            ma60 = market_slice.get("ma60", 0)
            diff = ma10 - ma60
            direction = "LONG" if diff > 0 else "SHORT" if diff < 0 else "FLAT"
            conf = min(1.0, abs(diff) / (market_slice.get("close", 1)))
        res = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction.upper(),
            edge=conf,
            expected_rr=1.0 + conf,
            evidence=[f"llm_conf={conf:.3f}"]
        )
        vec = [market_slice.get("ma10",0), market_slice.get("ma60",0), conf]
        self.memory.add(vec, {"ts": res.ts.isoformat(), "direction": res.direction, "edge": res.edge})
        return res
