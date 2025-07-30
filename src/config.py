import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self, path: str = "config.yaml"):
        with open(path, 'r') as fh:
            raw = yaml.safe_load(fh)
        self.mode = raw.get('mode', 'backtest')
        self.kucoin = raw.get('kucoin', {})
        # Replace env placeholders
        for key, value in list(self.kucoin.items()):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_key = value.strip('${}').strip()
                self.kucoin[key] = os.getenv(env_key)
