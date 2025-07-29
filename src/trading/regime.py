from dataclasses import dataclass
from typing import Dict

@dataclass
class Regime:
    name: str


class MarketRegimeClassifier:
    """Classify current market regime using simple heuristics."""

    def classify(self, features: Dict) -> Regime:
        trend = "Trending" if features.get("trend_strength", 0) > 0.6 else "Choppy"
        vol = "HighVol" if features.get("volatility_state", 0) > 0.6 else "LowVol"
        return Regime(name=f"{trend}-{vol}")
