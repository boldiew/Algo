import os
import json
from datetime import datetime
from dataclasses import asdict
from typing import Dict, List
from .agents.base import AgentResult

class StateStore:
    """Persist agent histories and exposures for recovery."""

    def __init__(self, path: str = "state.json"):
        self.path = path
        self.state = {
            "agents": {},
            "weights": {},
            "exposures": {},
            "day_pnl": 0.0,
            "intraday_pnl": 0.0,
            "open_trades": [],
            "trade_log": [],
        }
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.state = json.load(f)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.state, f)

    def load_agent_history(self, name: str) -> List[AgentResult]:
        records = self.state.get("agents", {}).get(name, [])
        res: List[AgentResult] = []
        for r in records:
            r["ts"] = datetime.fromisoformat(r["ts"])
            res.append(AgentResult(**r))
        return res

    def store_agent_history(self, name: str, history: List[AgentResult]):
        self.state.setdefault("agents", {})[name] = [
            {**asdict(r), "ts": r.ts.isoformat()} for r in history
        ]

    def load_weights(self) -> Dict[str, float]:
        return self.state.get("weights", {})

    def store_weights(self, weights: Dict[str, float]):
        self.state["weights"] = weights

    def load_exposures(self) -> Dict[str, float]:
        return self.state.get("exposures", {})

    def store_exposures(self, exposures: Dict[str, float]):
        self.state["exposures"] = exposures

    def load_pnl(self) -> Dict[str, float]:
        return {"day": self.state.get("day_pnl", 0.0), "intraday": self.state.get("intraday_pnl", 0.0)}

    def store_pnl(self, day: float, intraday: float):
        self.state["day_pnl"] = day
        self.state["intraday_pnl"] = intraday

    def load_open_trades(self) -> List[dict]:
        return self.state.get("open_trades", [])

    def store_open_trades(self, trades: List[dict]):
        self.state["open_trades"] = trades

    def load_trade_log(self) -> List[dict]:
        return self.state.get("trade_log", [])

    def store_trade_log(self, log: List[dict]):
        self.state["trade_log"] = log
