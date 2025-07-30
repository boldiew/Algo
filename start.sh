#!/bin/bash
set -e
python -m trading.main --mode backtest &
uvicorn trading.dashboard:app --host 0.0.0.0 --port 8000
