import logging
import pandas as pd
from kucoin_client import KucoinClient

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, config):
        self.config = config
        kc = config.kucoin
        self.client = KucoinClient(kc.get('key'), kc.get('secret'), kc.get('passphrase'), kc.get('base_url'))
        self.backtest_orders = []

    def execute(self, order: dict, tick: pd.Series = None):
        mode = self.config.mode
        if mode == 'backtest':
            return self._simulate_order(order, tick)
        elif mode == 'paper':
            logger.info('Paper trade %s', order)
            return {'status': 'paper', 'order': order}
        elif mode == 'live':
            result = self.client.place_order(order['symbol'], order['side'], order['size'], order['price'])
            logger.info('Live order result %s', result)
            return result
        else:
            raise ValueError(f'Unknown mode {mode}')

    def _simulate_order(self, order: dict, tick: pd.Series):
        fill_price = tick['price'] if tick is not None else order['price']
        executed = {**order, 'price': fill_price, 'filled': True}
        self.backtest_orders.append(executed)
        logger.debug('Backtest fill %s', executed)
        return executed
