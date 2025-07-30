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


def load_config(config_path: str | None = None) -> Config:
    """Load configuration from YAML and environment variables.

    The config path can be provided as an argument or via the ``CONFIG_PATH``
    environment variable. If the file is not found relative to the current
    working directory, the loader also checks the repository root so the
    application can be executed from any location.
    """
    load_dotenv()
    path = Path(config_path or os.getenv("CONFIG_PATH", "config.yaml"))
    if not path.exists():
        repo_path = Path(__file__).resolve().parents[2] / path.name
        if repo_path.exists():
            path = repo_path
        else:
            raise FileNotFoundError(f"Config file {path} missing")
    data = yaml.safe_load(path.read_text())
    mode = os.getenv("MODE", "backtest")
    kucoin = {
        "api_key": os.getenv("KUCOIN_API_KEY", ""),
        "secret": os.getenv("KUCOIN_SECRET", ""),
        "passphrase": os.getenv("KUCOIN_PASSPHRASE", ""),
        "base_url": os.getenv("KUCOIN_BASE_URL", "https://api-futures.kucoin.com"),
    }
    os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    return Config(mode=mode, risk=data.get("risk", {}), pairs=data.get("pairs", []), kucoin=kucoin)
