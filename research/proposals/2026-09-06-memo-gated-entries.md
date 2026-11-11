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

---

## Decision 2026-11-11: rejected

Not implemented, and it should not be. The proposal's own "why it might be
wrong" section turned out to be the whole story, and two months of record now
say so:

1. **It would have frozen the book.** The desk has been paused since
   21 September. `python -m kismat validate-memos` today: 20 valid memos, **0
   fresh enough for the engine to blend**. A rule that requires a `long` memo
   dated within 3 days before any new entry would have blocked **every entry
   for the last seven weeks**. It makes the systematic engine depend on an
   agent process that stops, and that dependency is silent — no error, just no
   trades.
2. **Entries were never the problem.** The 80-trade record shows the loss sat
   entirely in the exit rule: 54 trend-break exits, 0 winners, -779.90. Gating
   entries harder would not have recovered a cent of it.
3. **The research layer still has no measured edge.** Research-attributed P&L
   remains zero. Giving a layer with no demonstrated edge veto power over one
   that backtests at +84.6% over five years is backwards.

The narrow part of the concern was real and is now fixed differently: a `flat`
memo used to quietly cut the systematic score by 40% (see
`2026-09-19-conviction-means-two-things.md`). It now abstains. So `flat` no
longer blocks entries by accident, which is the correct resolution — `avoid`
keeps its explicit veto, and that is the only place research should hold a gate
until it has earned more.

Revisit only if research-attributed P&L becomes measurably positive.
