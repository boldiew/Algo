import sys, os; sys.path.insert(0, os.path.abspath("src"))
from feature_fabric import FeatureFabric


def test_funding_rate_zscore():
    ff = FeatureFabric(window=3)
    rates = [0.01, 0.02, 0.03]
    scores = [ff.funding_rate_zscore(r) for r in rates]
    assert scores[-1] != 0


def test_depth_weighted_mid_price():
    bids = [[100.0, 2], [99.5, 1]]
    asks = [[100.5, 2], [101.0, 1]]
    price = FeatureFabric.depth_weighted_mid_price(bids, asks)
    assert 99.0 < price < 101.0
