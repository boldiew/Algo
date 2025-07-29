from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat_completion

class SentimentAgent(BaseAgent):
    name = "Sentiment"

    def __init__(self):
        super().__init__()

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = f"Market data: {market_slice}. Provide sentiment LONG/SHORT/FLAT and confidence 0-1."
        try:
            text = await chat_completion(prompt, system="You are a crypto sentiment analyst")
            direction, conf = text.split()[0], float(text.split()[1])
        except Exception:
            ret = market_slice.get("return", 0.0)
            direction = "LONG" if ret > 0 else "SHORT" if ret < 0 else "FLAT"
            conf = min(1.0, abs(ret) * 10)
        res = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction.upper(),
            edge=conf,
            expected_rr=1.0 + conf,
            evidence=[f"llm_conf={conf:.3f}"]
        )
        vec = [market_slice.get("return",0), market_slice.get("sentiment",0), conf]
        self.memory.add(vec, {"ts": res.ts.isoformat(), "direction": res.direction, "edge": res.edge})
        return res
