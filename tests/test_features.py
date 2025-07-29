import numpy as np
import pandas as pd
from trading.features import hurst_exponent


def test_hurst_range():
    data = pd.Series(np.cumsum(np.random.randn(500)))
    h = hurst_exponent(data)
    assert 0 <= h <= 2
