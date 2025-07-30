import numpy as np
import pandas as pd
from trading.features import hurst_exponent, FeatureFabric


def test_hurst_range():
    data = pd.Series(np.cumsum(np.random.randn(500)))
    h = hurst_exponent(data)
    assert 0 <= h <= 2


def test_funding_z():
    ff = FeatureFabric()
    vals = [0.001 * i for i in range(1, 6)]
    z_vals = []
    for v in vals:
        z = ff._funding_z(v)
        z_vals.append(z)
    assert len(z_vals) == 5
    assert abs(z_vals[-1]) < 3
