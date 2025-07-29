import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
from ..memory import MemoryStore

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
    history: List[AgentResult] = field(default_factory=list)
    weight: float = 1.0
    memory: MemoryStore

    def __init__(self):
        self.history = []
        self.weight = 1.0
        self.memory = MemoryStore(path=f"{self.name}.index", dim=10)

    @abc.abstractmethod
    async def analyze(self, market_slice: Dict) -> AgentResult:
        """Run analysis and return an AgentResult."""

    def record(self, result: AgentResult):
        self.history.append(result)
