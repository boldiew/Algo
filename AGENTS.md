# AGENTS.md
# Project Directive for AI Agents (Codex, Claude, Gemini, Perplexity, Grok)

## PRIMARY GOAL
You are NOT allowed to create demos, placeholders, stubs, or speculative mockups.

You MUST build a complete, production-ready, fault-tolerant, and logic-heavy multi-agent AI crypto trading system, designed for live, continuous execution on KuCoin Futures with modular extensibility.

## KEY RULES

1. **System must not be lightweight.**
   - Do not return sample files, minimal code, or prototype agents.
   - Everything must use real algorithms, real risk logic, real API calls.
   - Never say "lightweight", "basic", "starter", or "skeleton".

2. **Every agent must be a real AI-powered class.**
   - Each agent (Sentiment, Technical, Fundamentals, Macro, Options-Flow) must interface directly with its assigned LLM API.
   - Responses must be parsed, scored, and evaluated in real-time.
   - Maintain memory of predictions and outcomes for self-recalibration.

3. **Feature Fabric must compute real-world derived metrics from streaming market data.**
   - You must implement computation for:
     - OHLCV deltas
     - Order book imbalance
     - Depth-weighted mid price
     - Realized volatility across windows
     - Funding-rate Z-scores
     - Return entropy
     - Hurst exponent
     - Sentiment signals from news/socials

4. **All live data must be normalized with a single event-time index.**
   - Fill gaps ≤ 60s, mask longer gaps.
   - Backfill data intelligently during startup or recovery.

5. **Regime classifier must determine the correct market regime every 60s.**
   - Inputs include ADX, regression R², volatility vs median, spread × depth, return entropy.
   - Output: 4 possible regimes → linked to separate strategy banks.

6. **Strategy banks must be hardcoded and logic-rich.**
   - No heuristic placeholders.
   - Strategies must publish full trade plans: entry/exit, stop-loss %, TP %, duration.
   - Strategy logic must reflect realistic trading behavior for each regime:
     - MOM-ATR-Break (Trending High Vol)
     - Pullback-EMA (Trending Low Vol)
     - VWAP-MeanRev (Choppy High Vol)
     - Grid-Range (Choppy Low Vol)

7. **Consensus engine must compute weighted edge, apply logistic sharpening, handle direction conflict.**
   - Block trade if:
     - Edge < 0.55
     - Direction disagreement > 40% of weight
   - Reduce size: `(1 - edge)²`

8. **Risk engine must include:**
   - Daily drawdown cap (-2%)
   - Intraday drawdown cap (-3%)
   - Correlated exposure cap (1.5× per pair)
   - Liquidation buffer (10% equity)

9. **No trades must be lost on restart.**
   - You MUST implement a `StateStore` to persist:
     - Agent histories
     - Open trades
     - Agent weights
     - Trade logs
   - Auto-restart must restore last known state.

10. **Nightly learning loop must run daily.**
    - Maximize Sharpe (adjust agent weights)
    - Archive underperforming strategies
    - Explore new parameters to fill the void

11. **Web Dashboard must be live-updating and secure.**
    - Use FastAPI + WebSockets or similar
    - Must show:
      - PnL
      - Active trades
      - Heatmap of agent edges
      - Timeline of regimes

12. **Secrets and config**
    - Secrets go in `.env`
    - Config goes in `config.yaml`
    - Mode selected with `--mode=backtest|paper|live`

13. **Backtest mode must share same codepath as live.**
    - Simulate ticks in real-time from historical data.
    - Inject edge cases and latency conditions.

14. **Observability**
    - Emit structured logs (`agent_output`, `strategy_signal`, `order_sent`, `order_fill`, `risk_violation`)
    - Alerts on errors, missed trades, or anomalies

15. **Compliance**
    - Follow Indian tax tagging
    - Never log secrets
    - Include LICENSE file and audit trail

## HARD BANS

- No stub APIs
- No dummy models
- No empty classes
- No "to be implemented later" comments
- No fake KuCoin signature
- No skipping performance tracking
- No skipping derived feature computation

## ACCEPTANCE CRITERIA

- 90-day BTC backtest: Sharpe ≥ 2
- 24-hour paper test: zero unhandled exceptions
- Live run: trades executed in all 4 regimes
- Process kill → full recovery in under 60 seconds
- All files + tests + README + LICENSE + `.env.sample` + `config.yaml` present

## FINAL MANDATE

This system is to be **plug-and-play**, production-grade, adaptive, and live-tradable.

If you’re not building that, you’re wrong.
