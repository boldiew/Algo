import sys, os; sys.path.insert(0, os.path.abspath("src"))
import pandas as pd
from kucoin_stream import UnifiedIndex


def test_gap_handling():
    idx = UnifiedIndex()
    first = idx.add(0)
    second = idx.add(1000)
    assert len(idx.index) == 2
    assert idx.index[0] == first
    assert idx.index[1] == second
    big_gap = idx.add(70000)
    assert idx.index[-1] is big_gap
    assert idx.index[-2] is pd.NaT
