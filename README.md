
# Algo Trading Platform

This repository contains a lightweight but extensible cryptocurrency futures trading system. It integrates live market data ingestion, multiple AI-driven analysis agents, adaptive regime classification and strategy selection, dynamic risk controls and automated order execution. Agent performance is tracked so their influence on trading decisions adjusts automatically over time.
Derived metrics include OHLCV deltas, realised volatility surfaces, return entropy and the Hurst exponent. State is checkpointed to `state.json` so the system can resume after interruptions. A FastAPI dashboard exposes real-time PnL and agent weights.

## Quick Start
1. Copy `.env.example` to `.env` and provide your KuCoin API credentials. For LLM providers you can list multiple keys comma separated using variables like `OPENAI_API_KEYS`.
2. Adjust `config.yaml` for risk limits and trading pairs.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the platform in one of three modes:
   ```bash
   python -m trading.main --mode backtest  # or paper, live
   ```
5. Start the dashboard:
   ```bash
   uvicorn trading.dashboard:app --port 8000
   ```

## Project Layout
- `src/trading` – core package containing agents, exchange connectors, data ingestion, risk logic and main orchestration code.
- `config.yaml` – user editable configuration for risk and symbols.
- `.env.example` – template for required environment variables.

## Tests
Run all unit tests with:
```bash
pytest -q