# Going live with real money: the gate

Date: 2026-11-11
Owner asked: "I will provide you the real account with real money ... we have to grow."

This is my answer, written down so it can be held against evidence rather than
re-argued. Short version: **not yet, and here is exactly what has to be true
first.** Every gate below is a number you can check, not a judgement call.

## Where the book actually stands today

| measure | value |
|---|---|
| paid in | 10,000.00 |
| equity | 8,996.36 |
| return | **-10.0%** over 66 days |
| peak / drawdown | 10,383.15 / **-13.4%** |
| closed trades | 80 |
| realised | **-1,282.79** |
| win rate | **10%** (8 of 80) |

That is the record. It is not a bad patch in a good system; a 10% win rate
against the 39-43% the same parameters backtest at means the live system was
not doing what the backtest tested. It wasn't: the trend-break exit was taking
54 of the 80 exits and winning none of them.

Nothing here has earned real money yet. Putting capital in on this record would
be paying for the privilege of finding out.

## What changed today

Five defects fixed, all found in the live record:

1. `trend_break_exit: false` — 54 exits, 0 winners, -779.90, 61% of all loss.
2. Flat memos abstain instead of taking a 40% haircut off the systematic score.
3. Alpaca exits clear stale orders first, so the ledger and the broker stop diverging.
4. The packet's `rs` column is populated after 66 days empty.
5. The memo schema and validator agree, and `us_etfs` is legal.

All five are verified against backtests and tests. **None has traded a single
live bar.** That distinction is the whole reason for the gate below.

## The gate

Real money goes in only when every one of these is true. Not most.

- **G1 — the fixes are actually running.** Merged to `main` and visible in the
  cycle log. Right now they cannot even be pushed: this session's GitHub
  credential has no write access.
- **G2 — a real post-fix sample.** At least **6 weeks** and **30 closed
  trades** with the fixes live. The fixes cut trade count by roughly half, so
  this takes longer than it used to.
- **G3 — win rate at or above 30%.** Backtest says 39-43%. Below 30% means the
  live system still is not the tested system, and the gate fails no matter what
  the return did.
- **G4 — realised P&L positive over that window**, with per-trade expectancy no
  worse than half the backtest's. Unrealised gains do not count; open positions
  are an opinion, closed trades are a record.
- **G5 — ledger equals broker.** `python -m kismat venue-check` clean, zero
  `ledger-only exit` lines in the window. Until this holds, every number above
  is bookkeeping, not fact. This one is non-negotiable: it is the difference
  between a track record and a spreadsheet.
- **G6 — drawdown inside the tested range.** Peak-to-trough no worse than -15%
  over the window; the fixed parameters backtest at -11.7%.
- **G7 — the kill switch tightened first.** `max_drawdown_pct` is **0.25**,
  which `config/risk.yaml` itself says is a paper-test setting and should go to
  **0.05-0.10 before live**. A 25% kill switch on real money means losing a
  quarter of it before anything stops.
- **G8 — the account is big enough to carry the desk.** `research/viability.md`
  puts this desk at $90-240/month. On a $10k account that is 11-29% a year
  against a strategy that backtests at ~15.8% CAGR: the research desk eats the
  entire edge. Either the account is nearer **$127,000**, or the desk runs
  weekly instead of daily, or it runs off and the systematic engine trades
  alone. Below that size the honest configuration is **engine on, desk off**.

## When the gate passes

Start at the smallest amount the broker will accept, not the full account. Run
it for a month at that size and compare the live fills against what the paper
ledger said would happen on the same bars; slippage and partial fills on real
money are the one thing no backtest here has tested. Scale only after that
matches.

## Two things I will not do

- **I will not place trades.** The risk engine in `config/risk.yaml` sizes and
  vetoes every order. That stays true on a real account.
- **I will not treat a reminder as approval.** You asked to be reminded about
  the real account and I have set that for **2026-12-09**, by which point the
  fixes should have ~4 weeks of live paper behind them. When it fires I will
  report each gate above as pass or fail with the numbers, and if they fail I
  will say so rather than find a way to call it ready.

## On "we have to grow"

The growth lever right now is not better stock picking. My memos have moved the
account by a measurable **zero**, and as of today **0 of 20 memos are fresh
enough for the engine to blend at all** — the desk has been paused since
21 September. The lever was a one-line exit rule that was quietly losing
-779.90, and the slots-and-stops change the walk-forward has been pointing at
since 7 September. Fix the machine first, then feed it research, then add money.
That order is the fastest path to growth that does not risk the capital.
