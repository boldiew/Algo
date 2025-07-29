import os
import asyncio
from datetime import datetime
from .config import Config
from .ingestion import KucoinDataStream
from .agents.sentiment import SentimentAgent
from .agents.technical import TechnicalAgent
from .agents.fundamentals import FundamentalsAgent
from .agents.macro import MacroAgent
from .agents.options_flow import OptionsFlowAgent
from .coordination import MultiAgentCoordinator
from .regime import MarketRegimeClassifier
from .strategies import STRATEGY_MAP
from .risk import RiskEngine
from .execution import ExecutionEngine
from .exchange import KucoinClient
from .state import StateStore


class TradingPlatform:
    def __init__(self, config: Config):
        self.config = config
        self.client = KucoinClient(
            api_key=os.getenv("KUCOIN_API_KEY", ""),
            secret=os.getenv("KUCOIN_SECRET", ""),
            passphrase=os.getenv("KUCOIN_PASSPHRASE", ""),
        )
        self.stream = KucoinDataStream(self.client, config.pairs)
        self.state = StateStore()
        self.agents = [
            SentimentAgent(),
            TechnicalAgent(),
            FundamentalsAgent(),
            MacroAgent(),
            OptionsFlowAgent(),
        ]
        self.classifier = MarketRegimeClassifier()
        self.risk = RiskEngine(config.risk)
        self.coordinator = MultiAgentCoordinator(self.agents)
        # restore state
        for agent in self.agents:
            agent.history = self.state.load_agent_history(agent.name)
        weights = self.state.load_weights()
        for agent in self.agents:
            if agent.name in weights:
                agent.weight = weights[agent.name]
        self.risk.exposures = self.state.load_exposures()
        pnl = self.state.load_pnl()
        self.risk.day_pnl = pnl["day"]
        self.risk.intraday_pnl = pnl["intraday"]
        self.execution = ExecutionEngine(self.client)
        self.last_optimisation_day = None

    def optimise_weights(self):
        for agent in self.agents:
            edges = [r.edge for r in agent.history[-100:]]
            if not edges:
                continue
            mean = sum(edges) / len(edges)
            var = sum((e - mean) ** 2 for e in edges) / len(edges)
            sharpe = mean / (var ** 0.5 + 1e-9)
            agent.weight = max(0.1, sharpe)

    async def handle_slice(self, market_slice: dict):
        consensus = await self.coordinator.decide(market_slice)
        if consensus.edge < 0.55:
            return
        regime = self.classifier.classify(market_slice)
        strat_fn = STRATEGY_MAP.get(regime.name)
        if not strat_fn:
            return
        trade_signal = strat_fn(market_slice)
        trade_signal.side = consensus.direction
        trade_signal.quantity *= (consensus.edge ** 2)
        if self.risk.allows_trade(trade_signal.symbol, trade_signal.quantity):
            await self.execution.place_order(trade_signal)
            self.risk.record_fill(trade_signal.symbol, trade_signal.quantity, 0.0)
        else:
            print("Risk limits hit, trading paused")
        for agent in self.agents:
            self.state.store_agent_history(agent.name, agent.history)
        self.state.store_weights({a.name: a.weight for a in self.agents})
        self.state.store_exposures(self.risk.exposures)
        self.state.store_pnl(self.risk.day_pnl, self.risk.intraday_pnl)
        self.state.save()

    async def run(self):
        async for data in self.stream.stream():
            await self.handle_slice(data)
            now = datetime.utcnow()
            if self.last_optimisation_day != now.date() and now.hour == 0:
                self.optimise_weights()
                self.last_optimisation_day = now.date()
