# Proposal: gate new entries on a fresh long memo

- date: 2026-09-06
- author: council/weekly-review
- status: proposed (not implemented; no change made to config/ or kismat/)

## Observation
Every decision in state/journal/decisions.jsonl carries `"research": null`. All six
opening trades on 2026-09-06 were made on the systematic score alone. Memos currently
influence the engine in only two ways: a decayed score contribution, and a veto when a
memo is `avoid` with conviction >= 0.7 (kismat/research/memos.py: `score`,
`vetoes_entry`). Nothing stops the engine opening a position the research desk has
explicitly called `flat`.

Today that gap is live: the council returned `long` on NVDA and MSFT and `flat` on AMZN,
SPY, ANZ.AX and BHP.AX — four of six positions the engine had already bought.

## Proposed rule
Do not open a *new* position unless a memo for that symbol, dated within 3 days, has
direction `long`. Existing positions are unaffected: exits stay with the systematic
rules and the risk engine. `flat` blocks new entries only; `avoid` keeps its veto.

## Why it might be wrong
With zero closed trades there is no evidence the research layer beats the systematic
score it would override. A research desk that is merely more cautious will show up as
fewer trades and lower turnover, which is not the same as better returns. It also adds a
hard dependency: a day the council fails to run becomes a day the engine cannot open
anything.

## Test that decides it
Compare, over the next 30 trading days, the realised P&L of entries the engine takes
against the memo direction that would have existed. Concretely, log for every `buy`
the same-day memo direction (already available via the `research` field once memos are
wired), then split closed trades into `memo_long`, `memo_flat` and `memo_absent`.

Adopt if `memo_flat` entries underperform `memo_long` entries by a margin larger than
the fee drag, over at least 20 closed trades. Reject if `memo_flat` entries perform in
line or better, which would say the council is filtering out good systematic trades.

Until that sample exists this stays a proposal. Do not edit config/risk.yaml or the
engine on the strength of one day.
