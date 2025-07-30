import argparse
import logging
import pandas as pd
from config import Config
from execution_engine import ExecutionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingPlatform:
    def __init__(self, config: Config):
        self.config = config
        self.engine = ExecutionEngine(config)

    def run(self):
        mode = self.config.mode
        if mode == 'backtest':
            self._run_backtest()
        else:
            self._run_live()

    def _run_backtest(self):
        ticks = pd.read_csv('data/historical_ticks.csv')
        for _, tick in ticks.iterrows():
            order = {'symbol': 'BTC-USDT', 'side': 'buy', 'size': 1, 'price': tick['price']}
            self.engine.execute(order, tick)
        logger.info('Backtest complete %d orders', len(self.engine.backtest_orders))

    def _run_live(self):
        # In paper and live mode, fetch a single ticker for example
        import requests
        resp = requests.get(f"{self.config.kucoin['base_url']}/api/v1/ticker?symbol=BTCUSDTM")
        resp.raise_for_status()
        tick = resp.json()['data']
        order = {'symbol': 'BTC-USDT', 'side': 'buy', 'size': 1, 'price': float(tick['price'])}
        self.engine.execute(order, pd.Series({'price': float(tick['price'])}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default=None)
    args = parser.parse_args()
    cfg = Config()
    if args.mode:
        cfg.mode = args.mode
    TradingPlatform(cfg).run()
