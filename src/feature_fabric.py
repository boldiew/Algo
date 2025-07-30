import logging
from collections import deque
from typing import Dict, List

import numpy as np
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer

LOGGER = logging.getLogger(__name__)


class FeatureFabric:
    """Compute derived market features."""

    def __init__(self, window: int = 1440):
        self.funding_rates = deque(maxlen=window)
        try:
            import nltk
            nltk.download("vader_lexicon", quiet=True)
        except Exception as exc:  # pragma: no cover - network issues
            LOGGER.warning("NLTK download failed: %s", exc)
        self.sentiment = SentimentIntensityAnalyzer()

    def funding_rate_zscore(self, rate: float) -> float:
        self.funding_rates.append(rate)
        series = pd.Series(self.funding_rates)
        if len(series) < 2:
            return 0.0
        return (series.iloc[-1] - series.mean()) / (series.std() + 1e-8)

    @staticmethod
    def depth_weighted_mid_price(
        bids: List[List[float]], asks: List[List[float]]
    ) -> float:
        bid_prices, bid_sizes = zip(*bids)
        ask_prices, ask_sizes = zip(*asks)
        wb = np.average(bid_prices, weights=bid_sizes)
        wa = np.average(ask_prices, weights=ask_sizes)
        return (wb + wa) / 2

    def sentiment_score(self, texts: List[str]) -> float:
        scores = [self.sentiment.polarity_scores(t)["compound"] for t in texts]
        if not scores:
            return 0.0
        return float(np.mean(scores))

    def update(self, data: Dict) -> Dict:
        """Update fabric with a new data point and return features."""
        features = {}
        if data.get("topic", "").startswith("/contractMarket/fundingRate"):
            rate = float(data["data"]["fundingRate"])
            features["funding_rate_zscore"] = self.funding_rate_zscore(rate)
        if data.get("topic", "").startswith("/contractMarket/level2"):
            depth = data["data"]
            features["depth_weighted_mid"] = self.depth_weighted_mid_price(
                depth["bids"], depth["asks"]
            )
        if data.get("sentiment_texts"):
            features["sentiment_score"] = self.sentiment_score(
                data["sentiment_texts"]
            )
        return features
