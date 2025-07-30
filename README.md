# Algo Trading Platform

This project implements a production-ready multi-agent trading platform for KuCoin Futures. The platform supports backtesting, paper trading, and live execution modes specified via `config.yaml`.

## Setup

1. Copy `.env.sample` to `.env` and populate with your KuCoin credentials.
2. Edit `config.yaml` to select `backtest`, `paper`, or `live` mode.
3. Install requirements: `pip install -r requirements.txt`.
4. Run tests: `pytest`.
5. Start trading:
   ```bash
   python -m src.trading_platform --mode backtest
   ```
