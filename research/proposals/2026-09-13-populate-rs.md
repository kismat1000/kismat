# Proposal: populate the `rs` column in the research packet

- date: 2026-09-13
- author: council/weekly-review
- status: proposed (no code changed; `kismat/` is out of scope for this routine)

## Defect
The packet's signal table defines `rs = momentum minus the class benchmark's` in its own header
legend, and the value is `-` for all 49 symbols on 11, 12 and 13 September — every day since the
column appeared.

This is not cosmetic. `prompts/pattern_analyst.md` lists rs among the inputs the analyst reads and
builds a rule on it: "A laggard in a strong sector is not a buy because the sector is strong." With
the column empty, that rule cannot fire. For the last three runs I derived relative strength by
hand from the same table — subtracting SPY's 63-day momentum from each US name's — which works for
`us_stocks` and `us_etfs` and fails for crypto, where the table carries no benchmark at all.

Hand-derivation also changed a call: today's XLK memo is flat partly because XLK's +2.6% lags
SPY's +3.9%, a technology fund trailing the index while holding the largest technology companies.
That is the pattern analyst's own warning case, and it was only visible because it was computed
manually.

## Why this is the highest-value fix
`research/backtests/study-2026-09-12.md` tested ten variants and ranks **`+rs 0.15` first by
robustness at 0.79 against the live set's 0.53**, with better out-of-sample return (+27.1% against
+25.8%) on 670 trades. In the same table, relative strength at weight 0.15 has the best average
robustness of any setting tested (0.56), ahead of w_rs 0.0 at 0.47. The 52-week-high and squeeze
weightings both scored *worse* than leaving them off.

So the desk's own research says relative strength is the most promising unused signal, and the
desk cannot see it.

## Proposed change
Populate `rs` in the packet generator for every symbol that has a class benchmark, and state which
benchmark was used. `us_stocks` and `us_etfs` against SPY is the obvious default; `au_stocks`
needs an ASX benchmark; crypto needs BTCUSDT or an explicit "no benchmark" marker so the pattern
analyst knows it is absent rather than zero.

Separately, and only after rs is visible in the packet for a week or two, consider whether to add
it to the score at weight 0.15 as the study suggests. Those are two decisions, not one: making a
signal visible to the research layer is cheap and reversible, changing the engine's scoring is
neither.

## Why it might be wrong
A single ten-variant study is thin evidence for a scoring change, and the study's own verdict is
**keep** — `+rs 0.15` clears the robustness margin but the report still did not recommend
switching. None of that argues against *displaying* the number, which is the actual proposal here.
