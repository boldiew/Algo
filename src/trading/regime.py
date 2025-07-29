from dataclasses import dataclass
from typing import Dict
import numpy as np

@dataclass
class Regime:
    name: str


class MarketRegimeClassifier:
    """Classify market regime using derived metrics."""

    def classify(self, features: Dict) -> Regime:
        adx = features.get("adx", 0)
        r2 = features.get("r2", 0)
        vol = features.get("rv30", 0)
        median_vol = features.get("median_vol", vol)
        entropy = features.get("return_entropy", 0)
        spread_depth = features.get("spread_depth", 0)

        trending = adx > 25 and r2 > 0.5
        high_vol = vol > median_vol
        choppy = entropy > 2.0 or spread_depth > 0.05

        trend = "Trending" if trending and not choppy else "Choppy"
        vol_state = "HighVol" if high_vol else "LowVol"
        return Regime(name=f"{trend}-{vol_state}")
