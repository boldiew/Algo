# Algo Trading Platform

This repository implements a robust and extensible cryptocurrency futures trading system. It integrates live market data ingestion, multiple AI-driven analysis agents, adaptive regime classification and strategy selection, dynamic risk controls and automated order execution. Derived metrics include OHLCV deltas, realised volatility surfaces, return entropy and the Hurst exponent. State is checkpointed to `state.json` so the system can resume after interruptions. A FastAPI dashboard exposes real-time PnL and agent weights.

## Setup

```bash
conda env update --file environment.yml --name algo
conda activate algo
```

## Running

```bash
python -m src.run --mode=backtest
```

## Tests

```bash
flake8 .
pytest
```

## Quick Start
1. Copy `.env.example` to `.env` and provide your KuCoin API credentials. For LLM providers you can list multiple keys comma separated using variables like `OPENAI_API_KEYS`.
2. Adjust `config.yaml` for risk limits and trading pairs.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the platform in one of three modes:
   ```bash
   python -m trading.main --mode backtest  # backtest simulated data
   python -m trading.main --mode paper     # paper trade using live feeds
   python -m trading.main --mode live      # execute real trades
   ```
5. Start the dashboard in a separate terminal:
   ```bash
   uvicorn trading.dashboard:app --port 8000
   ```
   Navigate to `http://localhost:8000` to monitor PnL, active trades and agent status in real time.

## Project Layout
- `src/trading` – core package containing agents, exchange connectors, data ingestion, risk logic and orchestration code.
- `config.yaml` – user editable configuration for risk and symbols.
- `.env.example` – template for required environment variables.

## Tests
Run all unit tests with:
```bash
pytest -q tests
```
