from .base import BaseAgent, AgentResult
from datetime import datetime
from typing import Dict
from ..llm import chat

class SentimentAgent(BaseAgent):
    name = "Sentiment"

    async def analyze(self, market_slice: Dict) -> AgentResult:
        prompt = (
            "Given recent social media sentiment and news snippets, "
            "provide a trading direction (LONG, SHORT, FLAT) and confidence score between 0 and 1. "
            f"Current return: {market_slice.get('return', 0):.5f}."
        )
        resp = await chat(messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo")
        content = resp.choices[0].message.content.strip().upper()
        direction = "FLAT"
        edge = 0.5
        if "LONG" in content:
            direction = "LONG"
        elif "SHORT" in content:
            direction = "SHORT"
        for token in content.split():
            try:
                val = float(token)
                edge = max(0.0, min(1.0, val))
                break
            except ValueError:
                continue
        result = AgentResult(
            ts=datetime.utcnow(),
            symbol=market_slice.get("symbol", ""),
            direction=direction,
            edge=edge,
            expected_rr=1.0 + edge,
            evidence=[content]
        )
        await self.store_memory(result)
        return result
