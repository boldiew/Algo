import asyncio
from datetime import datetime
from typing import List, Dict, Any

from .agents.base import BaseAgent, AgentResult
from .consensus import compute_weights, weighted_consensus

class MultiAgentCoordinator:
    """Run agents concurrently and return consensus results."""

    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.transcripts: List[Dict[str, Any]] = []

    async def gather(self, market_slice: Dict) -> List[AgentResult]:
        tasks = [agent.analyze(market_slice) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        for agent, result in zip(self.agents, results):
            agent.record(result)
        return results

    async def decide(self, market_slice: Dict) -> AgentResult:
        results = await self.gather(market_slice)
        weights = compute_weights(self.agents)
        consensus = await weighted_consensus(self.agents, results, weights)
        self.transcripts.append({
            "ts": datetime.utcnow().isoformat(),
            "agents": {a.name: r.evidence for a, r in zip(self.agents, results)}
        })
        return consensus
