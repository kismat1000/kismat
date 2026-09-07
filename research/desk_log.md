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

## 2026-09-07 — council run

Packet: `research/packets/2026-09-07.md`. Monday, so no weekly review. Account is now
$10,073 equity across 12 positions — the owner added capital and the engine bought crypto
and two more US names overnight.

**Yesterday's open question is closed.** The ASX price discrepancy was not a feed fault. The
packet now states it plainly: all prices are USD, converted at AUDUSD 0.7211, with native
AUD in its own column. BHP.AX is A$63.16, which matches the ~A$63.5 reported in mid-August,
and ANZ.AX is A$37.85. The desk's data was right and yesterday's suspicion was wrong — the
packet just wasn't labelling its units. Both ASX memos are re-run today as real calls with
native-AUD levels.

**Picks: 8.** Six holdings with no memo (AAPL, BNBUSDT, ETHUSDT, LINKUSDT, QQQ, SOLUSDT),
plus ANZ.AX and BHP.AX re-run because the flag that made yesterday's memos non-actionable
cleared. No new candidates taken — CSL.AX (+68.3% 3m but RSI 74 and SMA50 not aligned) and
RIO.AX were available and both looked like chases.

**Deferred holdings** (fresh memo from 2026-09-06, nothing material changed): NVDA (long
0.62), MSFT (long 0.55), AMZN (flat 0.55), SPY (flat 0.60). One day old, too early to score.

| symbol | direction | conviction | note |
|---|---|---|---|
| LINKUSDT | long | 0.55 | Bottomline/600 banks, Schwab, Circle PoR; but +80% in 2 months, RSI 69, whale sent $7.6m to Coinbase 7 Sep |
| AAPL | flat | 0.60 | 9 Sep event in two days; sell-the-news base rate, China and Siri unresolved |
| QQQ | flat | 0.62 | RSI 42, +2.1% 3m; duplicates the AI exposure we already hold directly |
| ETHUSDT | flat | 0.60 | ETH product inflows −73–96% w/e 4 Sep; L2 fee leakage; SOL taking share |
| BNBUSDT | flat | 0.60 | No catalyst until the ~mid-Oct burn; mid-range vs every forecast; exchange-token risk |
| SOLUSDT | flat | 0.55 | SEC commodity-trust recognition 5 Sep is real, but flow sources contradict and price sits on support |
| ANZ.AX | flat | 0.50 | A$37.85 above the broker targets found; RBA 29 Sep two-sided; no catalyst until Nov |
| BHP.AX | flat | 0.50 | A$63.16 above RBC A$60 and Macquarie A$55; iron ore near the US$90/t downgrade level |

No `avoid` memo on any held position. `validate-memos`: 12 valid (8 new plus 4 carried).

**Backtest cited** (`research/backtests/2026-09-06.md`, 730 days, generated 08:20 yesterday).
This changed the crypto calls materially and is quoted in all four crypto memos: the crypto
sleeve returned **−6.4%, Sharpe −0.15, 17% win rate over 75 trades, −19.2% max drawdown**,
against us_stocks +7.6% (Sharpe 0.63) and au_stocks +3.7% (Sharpe 0.57) on the same rules.
Trend-break exits alone lost 1,028 across 39 crypto trades. The system has no demonstrated
edge trading crypto momentum, so every crypto conviction today is capped by that — including
LINKUSDT, which has the best fundamental story on the desk and still only gets 0.55.

**Macro (once for the day).** Unchanged in direction, sharper in detail. Fed 15–16 Sep with
futures at 58–66% for a *hike*, though Waller said on 3 Sep he leans to holding at 3.5–3.75%;
2-year at its highest since Jan 2025 and the 10-year ~4.8% after the +162k payrolls print;
oil near $100 and European gas at a three-year high on renewed Iran fighting; RBA 29 Sep with
NAB expecting a hike. New and specific to crypto: bitcoin ETFs took **$986.9M** in the week to
4 Sep while ETH, SOL, XRP and Hyperliquid product inflows fell **73–96%** — money is
consolidating into BTC and out of exactly the alts we hold. macro_conviction long: 0.35.

**Things that failed or need checking.**
- Contradictory evidence on SOL ETF flows: one source reports a 10–11 day inflow streak and
  $153.87M (strongest week since Oct 2025), another reports Solana product inflows down 73–96%
  in the week to 4 Sep. Both dated within days. Unresolved; the memo says so and sizes for it.
- The research layer is still behind the engine. Yesterday LINKUSDT was deferred as the one
  candidate over the pick cap; the engine bought it anyway and it is +9.9%. That is twice now
  that entries were made before the desk had an opinion, which is the gap
  `research/proposals/2026-09-06-memo-gated-entries.md` is about.

### 2026-09-07 — evening re-check (second trigger, same day)

The daily trigger fired again at 22:33 UTC on a day the council had already run at 09:39.
No new packet (still `2026-09-07.md`), and all 12 holdings had memos under a day old, so
re-running the full council would have been repeating fresh research. Checked what actually
changed in the intervening 13 hours instead.

**US markets were closed** — Labor Day. NYSE, Nasdaq, bonds and CME futures shut for the
session, so every US mark is identical to this morning and no US memo could have new
evidence behind it. AAPL, AMZN, MSFT, NVDA, QQQ, SPY, ANZ.AX, BHP.AX, ETHUSDT, SOLUSDT and
BNBUSDT all deferred on this morning's memos.

**One memo revised: LINKUSDT, long 0.55 → flat 0.55.** This morning's memo called it long
while flagging a whale sending $7.6m to Coinbase. The whale turns out to have sent
**2.41M LINK (~$26.04M) over three weeks**, and on-chain reporting has every wallet cohort
in net distribution for the first time since early June. External daily RSI14 is ~76 against
the packet's 69, with price above the upper Bollinger band. The adoption story improved on
the same day — DTCC's collateral platform targets a Q4 commercial launch, Chainlink prices
tokenised stocks on Coinbase — so the thesis is intact; the entry is not. Holding is fine,
adding is not. This morning's call was too generous on timing and the evening evidence says
so plainly.

**Price discrepancy, minor and unresolved:** our mark for LINKUSDT is 12.764 (down from the
packet's 13.455) while external quotes put it at $13.07–13.32 and *up* ~7.1% on the session.
Direction of travel disagrees, not just level. Probably snapshot timing or venue, but it is
the second data-labelling surprise in two days, so it is on the record.

**New walk-forward backtest** (`research/backtests/wf-2026-09-07.md`, 50 symbols, 96 variants,
21 windows). Verdict is **keep** the live parameters, and that is well earned: re-picking the
best set each window returned +57.8% against +102.0% for holding the live set — parameter
chasing lost. But the setting-level averages are lopsided and worth recording: slots n8 scores
0.62 robustness against n12 at **0.20**, and a 4.0 ATR stop scores 0.58 against 2.5 at **0.24**.
Live runs the least robust option on both axes, ranks 31 of 96, and carries the table's worst
drawdown at −23.6% — earned back through the best return, +86.0% with +21.5% out of sample.
Filed as `research/proposals/2026-09-07-slots-and-stops.md`, with the argument against it.
The 12-slot cap is currently binding: today it skipped AVAXUSDT, BTCUSDT, CSL.AX, LTCUSDT
and RIO.AX.

Equity 10,073 → 9,998 across the day, a −0.75% drawdown from peak, all of it crypto marks.
No `avoid` memo on any held position. `validate-memos`: 12 valid.
