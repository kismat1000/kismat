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
