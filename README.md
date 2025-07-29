# Algo Trading Platform

This repository contains a lightweight but extensible cryptocurrency futures trading system. It integrates live market data ingestion, multiple AI-driven analysis agents, adaptive regime classification and strategy selection, dynamic risk controls and automated order execution. Agent performance is tracked so their influence on trading decisions adjusts automatically over time.
Derived metrics such as returns, moving averages and order book imbalance are computed from incoming ticks. State is checkpointed to `state.json` so the system can resume after interruptions.

## Quick Start
1. Copy `.env.example` to `.env` and provide your KuCoin API credentials.
2. Adjust `config.yaml` for risk limits and trading pairs.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the platform in one of three modes:
   ```bash
   python -m trading.main --mode backtest  # or paper, live
   ```

## Project Layout
- `src/trading` – core package containing agents, exchange connectors, data ingestion, risk logic and main orchestration code.
- `config.yaml` – user editable configuration for risk and symbols.
- `.env.example` – template for required environment variables.

## Tests
Run all unit tests with:
```bash
pytest -q
```
