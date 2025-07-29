import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trading.config import load_config, Config


def test_load_config(tmp_path, monkeypatch):
    cfg = {"risk": {"daily_stop": -0.02}, "pairs": ["BTC-USDT"]}
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml.dump(cfg))
    monkeypatch.setenv("MODE", "paper")
    monkeypatch.setenv("KUCOIN_API_KEY", "k")
    monkeypatch.setenv("KUCOIN_SECRET", "s")
    monkeypatch.setenv("KUCOIN_PASSPHRASE", "p")
    config = load_config(str(cfg_file))
    assert isinstance(config, Config)
    assert config.mode == "paper"
    assert config.risk["daily_stop"] == -0.02
    assert config.kucoin["api_key"] == "k"
