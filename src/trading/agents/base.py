import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import faiss
import numpy as np
from ..llm import embed

@dataclass
class AgentResult:
    ts: datetime
    symbol: str
    direction: str
    edge: float
    expected_rr: float
    evidence: List[str]


class BaseAgent(abc.ABC):
    name: str
    history: List[AgentResult]
    weight: float
    _index: faiss.IndexFlatL2
    _mem_vectors: List[np.ndarray]

    def __init__(self):
        self.history = []
        self.weight = 1.0
        self._index = faiss.IndexFlatL2(1536)
        self._mem_vectors = []

    @abc.abstractmethod
    async def analyze(self, market_slice: Dict) -> AgentResult:
        """Run analysis and return an AgentResult."""

    def record(self, result: AgentResult):
        self.history.append(result)

    async def _embed(self, text: str) -> np.ndarray:
        vec = np.array(await embed(text), dtype=np.float32)
        return vec

    async def store_memory(self, result: AgentResult):
        for ev in result.evidence:
            vec = await self._embed(ev)
            self._index.add(vec.reshape(1, -1))
            self._mem_vectors.append(vec)

    def update_weight(self, window: int = 50):
        records = self.history[-window:]
        if not records:
            return
        edges = np.array([r.edge for r in records])
        mean = edges.mean()
        std = edges.std() + 1e-9
        sharpe = mean / std
        self.weight = max(0.1, sharpe)

    async def recall(self, text: str, k: int = 3) -> List[str]:
        if self._index.ntotal == 0:
            return []
        vec = await self._embed(text)
        dists, idxs = self._index.search(vec.reshape(1, -1), k)
        return [self.history[i].evidence[0] for i in idxs[0] if i < len(self.history)]
