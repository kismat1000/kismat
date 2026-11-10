# Turn the trend-break exit off

Date: 2026-11-10
Status: open, awaiting owner decision. Change is committed locally but CANNOT be pushed:
  this session's GitHub credential has no write access to kismat1000/kismat.
Affects: `config/risk.yaml` -> `trend_break_exit`

## The finding

`trend_break_exit: true` with `trend_break_days: 1` exits a position on a single
close below SMA50 while underwater. On a system whose entry signal is a 55-day
breakout, one close below a 50-day average is noise, not a trend change. It is
the largest single source of loss in the paper book, and it has been visible in
every weekly backtest since 2026-09-12 without ever being written up.

## Live evidence (paper book, 2026-09-06 -> 2026-11-09, 80 closed trades)

| exit reason | trades | realised P&L | winners |
|---|---|---|---|
| trend break | 54 | **-779.90** | **0 of 54 (0%)** |
| trailing stop | 26 | -502.89 | 8 of 26 (31%) |

Fifty-four exits, not one winner. The rule accounts for 61% of realised losses
and two thirds of all exits. Book-level: equity 9,005.84 against 10,000.00 paid
in (-9.94%), peak 10,383.15, now -13.26% off peak. Overall win rate 10% (8/80)
against the 35-40% the backtests predict for the same parameters -- the gap is
this rule converting would-be winners into losses before the trailing stop can
work.

## Backtest evidence (`research/backtests/2026-10-31.md`, same grid every week since 09-12)

| book | trend-break 1d (live) | trend-break off |
|---|---|---|
| all (50 symbols, 530d) | +13.8% / Sharpe 0.60 / win 35% / 228 trades | **+16.3% / 0.69 / 39% / 170** |
| us_stocks | **-3.9%** / -0.29 / win 26% | **+5.0%** / 0.46 / win 31% |
| crypto | -4.1% / -0.08 / win 22% | -3.4% / -0.04 / win 35% |
| au_stocks | +2.2% / 0.38 / win 29% | +3.4% / 0.55 / win 34% |

`off` wins on Sharpe and win rate in all four books, and on return in three. The
exception on return is nothing: au_stocks +2.2% vs +3.4% is also `off`'s way.
us_stocks is the clincher -- the rule flips +5.0% into -3.9%, an 8.9-point swing,
and us_stocks is the largest class in the live book.

The exit-reason lines say the same thing in every report ever produced: cumulative
trend-break P&L is negative in all of them (-1274.76, -1594.13, -730.44, -646.88
on 2026-09-12) while trailing stops are strongly positive (+2307.56, +2332.95,
+948.76). `trend_break_days: 3` does not fix it (+12.7% vs +16.3% for off).

## Reproduced independently (2026-11-10, this session, fresh Yahoo data)

Both legs run back to back on the *same* cached bars, so the only difference is
the flag:

| book | rule ON (live) | rule OFF (this change) |
|---|---|---|
| us_stocks, 296 days | **-6.6%** / Sharpe **-0.56** / DD -16.6% / win 25% / 143 trades | **+0.4%** / Sharpe **+0.11** / DD **-14.5%** / win 31% / 93 trades |
| all 50 symbols, 531 days | +9.3% / 0.43 / -15.4% / win 35% / 233 trades | **+13.3%** / **0.56** / -15.4% / win **38%** / 176 trades |

A 7.0-point swing on us_stocks, Sharpe from negative to positive, and the
drawdown gets *smaller*, not larger. This is the point worth being clear about:
turning the rule off is not a risk-for-return trade. It removes trades that lost
money, so exposure falls (143 trades to 93) and the worst drawdown improves.

## Recommendation

Set `trend_break_exit: false`. One variable, so the next six weeks of live
trades attribute cleanly. The trailing stop at 2.5 ATR remains the risk control,
and the drawdown does not worsen (-13.0% off vs -12.9% at 1d on the whole
universe): this gives up no downside protection, it only stops cutting winners.

Not bundled here, on purpose -- change one thing at a time:

- **`max_positions: 12 -> 8`.** The 2026-11-08 walk-forward ranks the live set
  **80th of 97** by robustness (score 0.19, best 1.00), down from 31st of 96 on
  09-07. Every one of the top 13 variants uses `n8`; most use `stop4.0`. This is
  the unimplemented 2026-09-07 `slots-and-stops` proposal, now with much stronger
  evidence. The book currently holds exactly 8 positions, so the change would
  force no liquidation today.
- **`stop_atr_multiple: 2.5 -> 4.0`,** for the same reason.

## Operational bug found alongside

Two exits failed at the venue with Alpaca `403 potential wash trade detected`
(DBC, MSFT) because a queued opposite-side order existed. The ledger recorded
the exit; Alpaca kept the position. Several other exits read
`alpaca-paper skipped: not held at alpaca; ledger-only exit`. The ledger and the
broker account have diverged. `python -m kismat venue-check` (and `venue-sync`)
exists for this and should be run before any of these numbers is used to judge a
venue-mirrored record. Filed here rather than fixed, since it touches `kismat/`.
