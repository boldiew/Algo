from typing import List
import json
from math import exp
from .agents.base import AgentResult, BaseAgent


def compute_weights(agents: List[BaseAgent], window: int = 20) -> List[float]:
    """Return adaptive weights based on each agent's recent edge."""
    weights: List[float] = []
    for agent in agents:
        hist = agent.history[-window:]
        if hist:
            mean_edge = sum(r.edge for r in hist) / len(hist)
        else:
            mean_edge = 1.0
        weights.append(max(0.1, agent.weight * mean_edge))
    return weights


def _debate(results: List[AgentResult], weights: List[float]) -> AgentResult:
    transcript = [f"{r.direction}:{r.edge:.2f}:{';'.join(r.evidence)}" for r in results]
    long_w = sum(w for r, w in zip(results, weights) if r.direction == "LONG")
    short_w = sum(w for r, w in zip(results, weights) if r.direction == "SHORT")
    if long_w == short_w:
        direction = "FLAT"
    else:
        direction = "LONG" if long_w > short_w else "SHORT"
    edge = abs(long_w - short_w) / sum(weights)
    with open("debate.log", "a") as f:
        f.write(json.dumps({"ts": results[0].ts.isoformat(), "transcript": transcript, "decision": direction, "edge": edge}) + "\n")
    return AgentResult(ts=results[0].ts, symbol=results[0].symbol, direction=direction, edge=edge, expected_rr=1+edge, evidence=transcript)


def weighted_consensus(results: List[AgentResult], weights: List[float] | None = None) -> AgentResult:
    if not results:
        raise ValueError("No agent results")
    if weights is None:
        weights = [1.0 for _ in results]
    total_w = sum(weights)
    edge_raw = sum(r.edge * w for r, w in zip(results, weights)) / total_w
    # Sharpen low edges using a logistic adjustment
    edge = 1 / (1 + exp(-10 * (edge_raw - 0.5)))
    directions = {}
    for r, w in zip(results, weights):
        directions[r.direction] = directions.get(r.direction, 0) + w
    ordered = sorted(directions.items(), key=lambda x: x[1], reverse=True)
    direction = ordered[0][0]
    if len(ordered) > 1 and ordered[1][1] > 0.4 * total_w:
        return _debate(results, weights)
    return AgentResult(
        ts=results[0].ts,
        symbol=results[0].symbol,
        direction=direction,
        edge=edge,
        expected_rr=sum(r.expected_rr * w for r, w in zip(results, weights)) / total_w,
        evidence=[ev for r in results for ev in r.evidence],
    )
