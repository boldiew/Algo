from typing import List
from math import exp
from typing import List
from .agents.base import AgentResult, BaseAgent
import openai


def compute_weights(agents: List[BaseAgent], window: int = 20) -> List[float]:
    """Return adaptive weights based on each agent's recent edge."""
    weights: List[float] = []
    for agent in agents:
        agent.update_weight(window)
        hist = agent.history[-window:]
        mean_edge = sum(r.edge for r in hist) / len(hist) if hist else 1.0
        weights.append(max(0.1, agent.weight * mean_edge))
    return weights


async def debate(agents: List[BaseAgent], results: List[AgentResult]) -> List[str]:
    messages = [
        {"role": "system", "content": "You are a trading ensemble debating directions."}
    ]
    for agent, res in zip(agents, results):
        messages.append({"role": "user", "name": agent.name, "content": ' '.join(res.evidence)})
    if not agents:
        return []
    resp = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=messages)
    summary = resp.choices[0].message.content
    for agent in agents:
        await agent.store_memory(AgentResult(results[0].ts, results[0].symbol, "FLAT", 0.0, 0.0, [summary]))
    return [summary]


async def weighted_consensus(agents: List[BaseAgent], results: List[AgentResult], weights: List[float] | None = None) -> AgentResult:
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
        await debate(agents, results)
        direction = "FLAT"
    return AgentResult(
        ts=results[0].ts,
        symbol=results[0].symbol,
        direction=direction,
        edge=edge,
        expected_rr=sum(r.expected_rr * w for r, w in zip(results, weights)) / total_w,
        evidence=[ev for r in results for ev in r.evidence],
    )
