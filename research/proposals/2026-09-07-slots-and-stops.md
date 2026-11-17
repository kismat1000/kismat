# Proposal: test n8 slots and the 4.0 ATR stop against the live n12 / 2.5 settings

- date: 2026-09-07
- author: council/desk
- status: proposed (not implemented; no change made to config/ or kismat/)
- source: research/backtests/wf-2026-09-07.md (50 symbols, 96 variants, 21 walk-forward windows)

## Observation
The walk-forward's own verdict is **keep** the live parameters, and that verdict is well
founded: re-picking the best set each window returned +57.8% against +102.0% for simply
holding the live set, so parameter-chasing lost. Nothing below argues with that.

But the setting-level averages, taken across every other setting, are lopsided in a way
the headline verdict does not surface:

| setting | live value | robustness | alternative | robustness |
|---|---|---|---|---|
| slots | n12 | **0.20** | n8 | **0.62** |
| stop | 2.5 ATR | **0.24** | 4.0 ATR | **0.58** |

The live configuration holds the least robust option on both axes, and it ranks 31 of 96
overall (score 0.63 against a best of 1.19) with the worst drawdown in the table, -23.6%.
It earns that rank on total return: +86.0% and +21.5% out of sample, both excellent.

So this is not "the live settings are wrong". It is "the live settings buy their return
with concentration and tight stops, and we have never tested whether we want that trade".
The 12-slot cap is also binding in practice right now: the portfolio journal shows
`max positions 12 reached` skipping AVAXUSDT, BTCUSDT, CSL.AX, LTCUSDT and RIO.AX today.

## Proposed test
Run the two single-setting changes in isolation rather than adopting the top-ranked
variant wholesale:

1. `n8` with everything else live (sma50/200 mom63 brk55 stop2.5).
2. `stop4.0` with everything else live (sma50/200 mom63 brk55 n12).

Compare against live on: robustness score, max drawdown, out-of-sample return, and share
of positive windows. Adopt a change only if it cuts max drawdown by more than 5 points
without giving up more than a third of out-of-sample return.

## Why it might be wrong
Robustness averaging across variants can be dominated by combinations we would never run.
The live set's high drawdown may also be the price of the return we actually want on a
small account trying to compound. And a wider stop (4.0 ATR) means larger per-trade dollar
risk at the same 1% sizing rule, which is not obviously safer in practice even if it tests
better - it survives noise by absorbing more loss.

No change to config/risk.yaml or the engine on the strength of one report.

---

## Decision 2026-11-11: not adopted, and the reason is worth keeping

Both legs tested properly on five years of real data, 97 variants, 21 windows.
Neither is adopted. This is a genuine trade-off, not a defect like the
trend-break exit, and I changed my mind on it during the session — the first
read of the aggregate looked like a clear win and it is not.

**Slots (12 -> 8).** For the live parameter family:

| | robustness | return | OOS | max DD |
|---|---|---|---|---|
| n12 (live) | 0.92 | **+84.6%** | +9.7% | -23.7% |
| n8 | **1.20** | +51.4% | **+13.7%** | **-21.9%** |

n8 is more robust, survives better out of sample and draws down less, but gives
up **33 points of return over five years**. The per-setting average table looks
much cleaner than this (n8 0.81 against n12 0.58 at equal return, -19.1% vs
-22.1% drawdown) because it averages across ~48 variants so the other
parameters cancel; for *this* set the return cost is real and the aggregate
hides it. Quoting the aggregate alone would have been misleading.

**Stops (2.5 -> 4.0).** Marginal: per-setting robustness 0.72 against 0.67,
return +40.3% vs +50.7%, drawdown -18.9% vs -22.3%. The top ranks are split
between the two (rank 1 is stop4.0, ranks 2-5 are stop2.5), unlike slots where
n8 is near-unanimous. A 0.05 robustness edge is not a reason to move a stop.

**Why neither ships now.**

1. **Attribution.** `trend_break_exit: false` is going live on evidence that is
   unambiguous and replicated everywhere, including 54 live exits with zero
   winners. Stacking an ambiguous parameter change on top means that if the
   next six weeks disappoint, we cannot tell which change did it. The go-live
   gate in `research/go-live.md` depends on reading that window cleanly.
2. **The two walk-forwards disagree.** CI's `wf-2026-11-08.md` ranks the live
   set **80 of 97**; this local run ranks it **28 of 97**. They are not
   comparable: this container cannot reach Yahoo's earnings endpoint
   ("earnings dates for 0 symbols"), so the `earnings_blackout_days: 7` rule
   that CI applies is absent here. I should not have quoted the 80-of-97 figure
   as settled yesterday without checking that.
3. **The report's own warning.** Re-picking the best set each window returned
   **+37.0%** against **+96.2%** for simply holding the live set. This grid
   punishes parameter chasing, and both runs say "consider", not "adopt".

Final config: trend-break off, `max_positions` 12, `stop_atr_multiple` 2.5.
Five years, whole universe: **+84.6% / Sharpe 0.82 / max DD -23.7% / win 39%**.

Revisit after the next CI walk-forward runs with the trend-break fix in place,
which is the first apples-to-apples test of slots in the environment the live
engine actually runs in. Full local report: `research/backtests/wf-2026-11-11-local.md`.
