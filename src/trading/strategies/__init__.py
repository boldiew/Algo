from . import trending_highvol, trending_lowvol, choppy_highvol, choppy_lowvol

STRATEGY_MAP = {
    "Trending-HighVol": trending_highvol.generate_signal,
    "Trending-LowVol": trending_lowvol.generate_signal,
    "Choppy-HighVol": choppy_highvol.generate_signal,
    "Choppy-LowVol": choppy_lowvol.generate_signal,
}
