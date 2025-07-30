from dataclasses import dataclass
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    mode: str
    risk: dict
    pairs: list
    kucoin: dict
    backtest_path: str | None = None


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML and environment variables."""
    load_dotenv()
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {config_path} missing")
    data = yaml.safe_load(path.read_text())
    mode = os.getenv("MODE", "backtest")
    kucoin = {
        "api_key": os.getenv("KUCOIN_API_KEY", ""),
        "secret": os.getenv("KUCOIN_SECRET", ""),
        "passphrase": os.getenv("KUCOIN_PASSPHRASE", ""),
        "base_url": os.getenv("KUCOIN_BASE_URL", "https://api-futures.kucoin.com"),
    }
    backtest_path = os.getenv("BACKTEST_DATA", data.get("backtest_data"))
    os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    return Config(
        mode=mode,
        risk=data.get("risk", {}),
        pairs=data.get("pairs", []),
        kucoin=kucoin,
        backtest_path=backtest_path,
    )
