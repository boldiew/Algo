from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat_completion

class MacroAgent(BaseAgent):
    name = "Macro"

    def __init__(self):
        super().__init__()

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = f"macro volatility {market_slice.get('vol')} and hurst {market_slice.get('hurst')}. Output LONG/SHORT/FLAT and confidence."
        try:
            text = await chat_completion(prompt, system="You are a macro analyst")
            direction, conf = text.split()[0], float(text.split()[1])
        except Exception:
            vol = market_slice.get("vol", 0)
            direction = "LONG" if vol < 0.01 else "SHORT"
            conf = min(1.0, abs(0.01 - vol) * 100)
        res = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction.upper(),
            edge=conf,
            expected_rr=1.0 + conf,
            evidence=[f"llm_conf={conf:.3f}"]
        )
        vec = [market_slice.get("vol",0), market_slice.get("hurst",0), conf]
        self.memory.add(vec, {"ts": res.ts.isoformat(), "direction": res.direction, "edge": res.edge})
        return res
