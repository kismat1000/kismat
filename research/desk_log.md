# Desk log

Running record of the research desk. Newest entries at the bottom.

## 2026-09-06 — access check

- `git pull` on `main`: worked, already up to date with `origin/main`.
- `git push --dry-run origin HEAD:main`: accepted ("Everything up-to-date", no rejection).
- Research tools available: WebSearch and WebFetch.
- Latest commit on main at check time: `2177dcb` "Merge PR #2: one-tap Telegram test alert workflow".
- No prompts run, no memos written, no files changed in that check.

## 2026-09-06 — council run

Packet: `research/packets/2026-09-06.md`. Macro run once for the day; bull, bear and
judge run per symbol. Sunday, so the weekly review ran too.

**Scanner picks.** The routine caps picks at five but also requires every open position.
There are six open positions, so the two rules conflict. I covered all six holdings —
reviewing live risk beats adding a new name — and deferred the one non-held candidate
that would otherwise have made the list, LINKUSDT (top systematic score +0.85, 55-day
breakout, fresh adoption headlines). It should be first in the queue tomorrow. Flagging
the conflict rather than silently dropping a position.

| symbol | direction | conviction | note |
|---|---|---|---|
| NVDA | long | 0.62 | Q2 FY27 beat 26 Aug: $96.2B rev, DC +117%, Q3 guide $108B ex-China |
| MSFT | long | 0.55 | Azure +43% cc and >$100B FY26; catalyst already fired, no event until late Oct |
| AMZN | flat | 0.55 | AWS +37%, best in 18 quarters, but capex TTM $169B (+64%) and price stalled |
| SPY | flat | 0.60 | Coin-flip FOMC 15–16 Sep; no edge buying index beta into it |
| BHP.AX | flat | 0.50 | Iron ore near the US$90/t downgrade level; price feed unverified |
| ANZ.AX | flat | 0.45 | RBA 29 Sep hike risk, no catalyst until Nov; price feed unverified |

No `avoid` memo on any held position. `python -m kismat validate-memos`: 6 valid, 0 invalid.

**Macro (applies to all six).** Mixed to risk-off. August payrolls +162k against +53k
expected, unemployment steady at 4.1%; the 2-year hit its highest since Jan 2025 and the
10-year moved to ~4.8%; FedWatch put a 25bp *hike* at 58–66% for 15–16 Sep, though Waller
said on 3 Sep he was inclined to hold at 3.5–3.75%. Renewed fighting in Iran has European
gas futures at a three-year high and oil near $100. RBA holds at 4.35% with a 29 Sep
decision and a live hike risk after a strong Q2 GDP print; NAB expects a September hike,
ANZ and CBA November, Westpac a hold. macro_conviction that the regime favours long
exposure: 0.35.

**Things that failed or need fixing.**
- Crypto primary feed geo-blocked: all ten crypto symbols logged `451 Client Error` from
  api.binance.com at 04:48. The fallback chain recovered and the levels look current
  (BTCUSDT 79,890 against reported $80–82k on 4 Sep), so this failed quietly.
- ASX price levels unreconciled: packet has ANZ.AX 27.3435 and BHP.AX 44.8519; dated
  commentary through Aug–Sep 2026 puts both materially higher (ANZ ~A$33–35, BHP ~A$63,
  broker targets A$55–67). US and crypto levels in the same packet do look current, so
  this is not obviously a whole-feed failure. Could not settle it here: Yahoo Finance
  egress is blocked from this session, so the desk's own source cannot be re-queried.
  Both ASX memos are flat and say no level-based call on those symbols is trustworthy
  until this is resolved. Highest-priority open question — about 30% of invested capital
  is marked at prices nobody has verified.
- `yfinance` and marketindex.com.au are both unreachable from the research session, which
  limits independent price verification generally, not just for ASX names.

**Weekly review.** `python -m kismat review` wrote `research/reviews/2026-09-06.md`;
the written review is `research/reviews/2026-09-06-review.md`. The account was seeded at
04:48 today, so there is no week to review: 0 closed trades, equity 1000.00 → 998.83
(−0.12%), all of it the $0.7355 in entry fees. Every decision carries `"research": null` —
no memo has ever changed a decision. Proposal filed at
`research/proposals/2026-09-06-memo-gated-entries.md` to gate new entries on a fresh
`long` memo, with the test that would decide it and the argument against it.
