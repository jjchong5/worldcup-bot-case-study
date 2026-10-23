# World Cup 2026 Prediction-Market Trading Bot

An automated pipeline that ran live on [Polymarket](https://polymarket.com)'s World Cup 2026 markets during the tournament: discover every market, estimate match probabilities, compare against live order-book prices, size and place orders, and reconcile positions against on-chain state after every run.

It traded a small real bankroll, built as a proof of concept for one question: **do publicly available soccer rating models carry a tradeable edge over market-implied odds?** (Short answer, from the [follow-up](#follow-up-skill-or-luck): no. The +42.8% was most likely luck.)

> **The model, sizing and strategy code are private.** This repo is the case study plus the reusable engineering pieces.

## Result

Every position settled by 2026-08-11. Figures come from the wallet's complete Polymarket activity log (every trade and redemption), not the bot's own ledger.

| | |
|---|---|
| Resolved trades | 43 |
| Return on starting bankroll | **+42.8%** |
| Trades won | 10 of 43 (it almost always bought the underdog) |
| Without the single largest win | about +3% |

One late winner (a knockout-stage win, England) supplied about 93% of the profit, and 43
underdog-heavy trades is far too small a sample to separate edge from variance on its own. A
follow-up analysis in October 2026 ([below](#follow-up-skill-or-luck)) answered the question:
**the models had no edge over the market, and the profit was most likely luck.** What the run did
prove is the engineering: a pipeline that found, sized, placed and reconciled real orders
through the tournament. What broke along the way is written up below.

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

## Follow-up: skill or luck?

Three months after the final, I tested the result four ways. Every test used only information
available before each match kicked off.

**1. Were the models better forecasters than the market?** No. For the 77 matches where the
bot logged a forecast before kickoff, I scored each forecaster with the Brier score, which
measures probability accuracy (lower is better):

| Forecaster | Brier score |
|---|---|
| Market price (overround removed) | **0.451** |
| Best single rating model | 0.467 |
| The blend the bot traded on | 0.471 |
| Other rating models | 0.474–0.478 |

The market beat every model.

**2. Did the bot buy at good prices?** No. A trader with real skill tends to buy before the
market moves their way. I compared each of the bot's 58 real buys with that share's price one
hour before kickoff:
- The price fell after 81% of the buys.
- Weighted by dollars, the average move was +0.7¢, which is effectively zero.

**3. Was the result robust?** No. I replayed the same rules, model and matches, but placed every
bet one hour before kickoff. A $1,000 bankroll ended at **$457**. Changing only when the bets
were placed flips a 43% gain into a 54% loss, which is the signature of luck rather than edge.

**4. Does it work outside one tournament?** No. A rebuilt version had cautious sizing
(quarter-Kelly, a 5% minimum edge, per-bet and total exposure caps) and home advantage for
non-neutral venues. I replayed it on 246 other national-team matches from August to October 2026.
The same $1,000 ended at $369. On the October matches the market's Brier score was 0.505 against
the model's 0.540; the 95% confidence interval for that gap excludes zero. Blending any amount of
the model into the market price made the forecast worse.

I also checked one model-free idea. In the October data, outcomes priced 40–60¢ seemed to win
more often than their price implied. I fixed the trading rules first, then tested them on
matches they had never seen:

| Data | Return |
|---|---|
| October internationals, where the pattern was spotted | +14% |
| World Cup | +4% |
| 537 club matches (European leagues, Champions League, Europa League, MLS) | −4% |

That is what a pattern found in noise looks like. For scale, buying every outcome at those
prices lost 7–14%. That's the cost of the fee, the bid–ask spread and the market's margin, which
any edge has to beat first.

**What I'd do differently.** Before risking money, score the model against the market price on
past matches; it has to beat the market, not just produce reasonable-looking numbers. Then check
whether entry prices beat the price at kickoff. Both tests are cheap and would have answered the
question before the tournament started. The rebuilt pipeline now runs as a paper trader,
logging forecasts, prices and results so any future idea can be scored the same way.

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
