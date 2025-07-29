from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat_completion

class OptionsFlowAgent(BaseAgent):
    name = "OptionsFlow"

    def __init__(self):
        super().__init__()

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = f"orderbook imbalance {market_slice.get('imbalance')} depth-mid {market_slice.get('depth_mid')}. Suggest LONG/SHORT/FLAT and confidence"
        try:
            text = await chat_completion(prompt, system="You analyse options flow and order book")
            direction, conf = text.split()[0], float(text.split()[1])
        except Exception:
            imb = market_slice.get("imbalance", 0)
            direction = "LONG" if imb > 0 else "SHORT" if imb < 0 else "FLAT"
            conf = min(1.0, abs(imb))
        res = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction.upper(),
            edge=conf,
            expected_rr=1.0 + conf,
            evidence=[f"llm_conf={conf:.3f}"]
        )
        vec = [market_slice.get("imbalance",0), market_slice.get("depth_mid",0), conf]
        self.memory.add(vec, {"ts": res.ts.isoformat(), "direction": res.direction, "edge": res.edge})
        return res
