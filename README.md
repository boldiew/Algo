# Algo Trading System

This repository implements a multi-agent cryptocurrency trading framework with real-time data ingestion from KuCoin Futures. The system computes advanced features using a unified event-time index and prepares inputs for AI-based strategy agents.

## Setup

```bash
conda env update --file environment.yml --name algo
conda activate algo
```

## Running

```
python -m src.run --mode=backtest
```

## Tests

```
flake8 .
pytest
```
