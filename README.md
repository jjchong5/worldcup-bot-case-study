# World Cup 2026 Prediction-Market Trading Bot

An automated pipeline that ran live on [Polymarket](https://polymarket.com)'s World Cup 2026 markets during the tournament: discover every market, estimate match probabilities, compare against live order-book prices, size and place orders, and reconcile positions against on-chain state after every run.

It traded a small real bankroll, built as a proof of concept for one question: **do publicly available soccer rating models carry a tradeable edge over market-implied odds?**

> **The model, sizing and strategy code are private.** This repo is the case study plus the reusable engineering pieces.

## Result

Every position settled by 2026-08-11. Figures come from the wallet's complete Polymarket activity log (every trade and redemption), not the bot's own ledger.

| | |
|---|---|
| Resolved trades | 43 |
| Return on starting bankroll | **+42.8%** |
| Trades won | 10 of 43 (it almost always bought the underdog) |
| Without the single largest win | about +3% |

So the answer to the question above is **not proven either way**. One late winner (a knockout-stage
win, England) supplied about 93% of the profit, and 43 underdog-heavy trades is far too small a
sample to separate edge from variance. What the run did prove is the engineering: a pipeline that
found, sized, placed and reconciled real orders through the tournament. What broke along the way is written up below.

## How it works

```
scheduler ─► discover markets ─► model ─► edge vs. live book ─► size ─► execute
   │          (paginated API,      (win/draw/   (depth-aware,        │       │
   │           classify shapes)     loss odds)   fill-realistic)     ▼       ▼
   │                                                          ledger ◄─ reconcile vs. chain
   └─ match-anchored runs (kickoff + settle window), failure alerts, run reports
```

- **Exhaustive discovery.** Series and tag pagination finds every World Cup market, including props and outrights; keyword search is avoided because it silently returns capped, contaminated results.
- **Fill-realistic edge.** Prices are compared at what an order of the intended size would actually pay after walking the live book, not at the midpoint.
- **Backtest data capture.** Polymarket has no historical order-book API, so the pipeline snapshots full-depth books and prices as it runs (hash-deduplicated to keep storage bounded) and a replay engine scores strategies afterwards.
- **Match-anchored scheduling.** Runs are keyed to kickoff times rather than a fixed interval, with an in-play guard that refuses new entries on matches already started.
- **Operations.** Telegram alerts on failed runs, per-phase timing in run reports, automatic collection shut-off after the tournament, and a position ledger reconciled against on-chain state each run.

## What I learned

Going live produced four incidents in a single day. I wrote up the pattern behind them, and nearly every bug fell into one of three classes:

1. **Silent fallbacks that mask failures.** A portfolio-value lookup returned zero for over 24 hours and was trusted, which zeroed every trade size with no error. The fix was a design rule: *when the real value is unknown, refuse to act.* Never assume zero.
2. **Unverified assumptions about external data.** A field that looked right (an event's end date used as its kickoff) made the system behave as if matches in progress had not started. Tick size was hardcoded instead of read per market, although the API already returned it. Both were wrong in a plausible way, so nothing crashed.
3. **Order-of-operations bugs in multi-step state.** These only appear when the whole sequence runs against real state, such as a SELL path missing a required parameter, which was found only when the exit path was first exercised live.

A bug I'm particularly glad I caught: the realized-P&L figure didn't reconcile against actual account equity. Tracing it showed the reconciler was matching resolved results by the wrong key (event ID versus per-outcome market ID), so winning positions were never credited and the reported P&L was silently understated. It surfaced only because I compared the report to account equity by hand, which is why I now treat reconciliation against an independent source as non-negotiable.

## What's in this repo

| Path | What it is |
|---|---|
| `pmkit/fills.py` | Volume-weighted fill-price estimation against a limit order book (buy and sell), used to make backtests and edge calculations fill-realistic |
| `pmkit/teamnames.py` | Team-name normalisation (flags, shortcodes, accents, aliases) for joining data from sources that spell names differently, with a guard against short-code false matches |
| `tests/` | Unit tests for both |

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Disclaimer

A hackathon and research project, not investment advice. It trades real money against a probabilistic model; models can be wrong and past performance does not guarantee future results.
