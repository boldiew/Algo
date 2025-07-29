from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat

class FundamentalsAgent(BaseAgent):
    name = "Fundamentals"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = (
            f"Funding rate z-score: {market_slice.get('funding_z', 0):.3f}, "
            f"Open interest change: {market_slice.get('d_volume', 0):.2f}. "
            "Return direction LONG/SHORT/FLAT and confidence." 
        )
        resp = await chat(messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo")
        msg = resp.choices[0].message.content.upper()
        direction = "FLAT"
        edge = 0.5
        if "LONG" in msg:
            direction = "LONG"
        elif "SHORT" in msg:
            direction = "SHORT"
        for token in msg.split():
            try:
                edge = float(token)
                break
            except ValueError:
                continue
        edge = max(0.0, min(1.0, edge))
        result = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[msg]
        )
        await self.store_memory(result)
        return result
