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

## 2026-09-08 — council run

Packet: `research/packets/2026-09-08.md`. Tuesday. Equity 9,958.65, 12 positions, cash 2,717.88.

**Two prior calls resolved, both the right way.** The engine exited both names the desk had
called flat, on trend breaks, before either thesis needed defending:
- **ANZ.AX** sold 05:47 at 26.54 on "trend break: below fast SMA and underwater" (entry 27.36,
  about −3.0%). The 7 Sep memo was flat 0.50 on no catalyst before November.
- **AAPL** sold 18:47 at 315.50 on the same rule (entry 320.13, about −1.4%) — the day *before*
  the 9 September iPhone event. The 7 Sep memo was flat 0.60 arguing precisely that owning
  Apple into its own event is the least favourable setup in large-cap tech. The event has not
  happened yet, so this is the exit being right, not the thesis being proven; the sell-the-news
  claim is still untested.

Also new: fills now carry `alpaca-paper` tags ("alpaca-paper filled @ 315"), so orders are
routing to a broker paper account rather than the internal simulator.

**Picks: 3.** Holdings with no memo in the last three days: **BTCUSDT** and **DBC**, both bought
in the last 24 hours. Plus **NVDA** re-run on a material change. No new candidates researched:
XLE (+0.47), XLF (+0.46) and XLV (+0.45) are all fresh ETF candidates, but the book is at its
12-position cap and the engine is already skipping entries for that reason, so memos on them
could not change a decision this week.

| symbol | direction | conviction | note |
|---|---|---|---|
| NVDA | flat | 0.55 | **Downgrade from long 0.62.** The 55-day breakout the 6 Sep memo relied on is gone; score +0.67 → +0.43 in two sessions |
| DBC | flat | 0.60 | Real hedge value, but RSI 75 at a 55-day high on a war premium the EIA and JPM both forecast lower |
| BTCUSDT | flat | 0.55 | Flows consolidating into BTC and away from alts, but range-bound $77–82k, RSI 53, no breakout |

**Deferred holdings** (memo under three days, nothing material): MSFT (long 0.55, 6 Sep — now
the *only* long memo on the desk), AMZN (flat 0.55), SPY (flat 0.60), QQQ (flat 0.62), ETHUSDT
(flat 0.60), BNBUSDT (flat 0.60), SOLUSDT (flat 0.55), LINKUSDT (flat 0.55), BHP.AX (flat 0.50).

No `avoid` memo on any held position. `validate-memos`: 14 valid.

**On downgrading NVDA.** This is the second long→flat downgrade in two days after LINKUSDT
last night, and two flips in two days deserves scepticism rather than a shrug. Both were
triggered by a condition the original memo named itself: LINKUSDT's memo flagged whale
distribution and the distribution turned out to be $26M over three weeks; NVDA's memo said
"price is confirming — a 55-day breakout" and the breakout flag is now absent with the score
nearly halved. Neither was a reaction to the price alone. Still worth watching: if this desk
downgrades every position the moment its score dips, it is a lagging indicator with extra
steps, and the calibration table in the Sunday review is where that will show up.

**Macro (once for the day).** Broadly unchanged, still hostile to duration. US index 7,707 on
8 Sep (−0.15%), Asia-Pacific closed red, Stoxx 600 −0.3%. The 10-year at 4.796% and the 2-year
at 4.394%, both higher again. FOMC is eight days out with a hike priced at 58–66%. Oil remains
near $100 on Hormuz constraints — but note both the EIA (~$85/b in 3Q26) and J.P. Morgan
($86 Q3, $80 Q4, $78 year-end) forecast Brent *below* spot, which is the single most useful
number found today and is what turned the DBC call flat. macro_conviction long: 0.35.

**Defect found: the memo schema cannot express our own universe.**
`config/universe.yaml` has four asset classes; `prompts/memo_schema.json` allows three, missing
`us_etfs`. DBC is an `us_etfs` symbol, so today's DBC memo is schema-invalid by the letter — and
`validate-memos` passed it anyway, because `kismat/research/memos.py: validate()` never checks
`asset_class` against the enum. The validator and the documented schema disagree. I used the
truthful value (`us_etfs`) rather than mislabelling a commodity-futures ETF as `us_stocks` to
pass a check. Filed as `research/proposals/2026-09-08-memo-schema-us-etfs.md`; not fixed here,
since `prompts/` changes belong in their own pull request.

## 2026-09-09 — council run

Packet: `research/packets/2026-09-09.md`. Wednesday. Equity 9,835.72, 12 positions, cash 1,685.53.
Equity has fallen four sessions running (10,073 → 9,836, −2.4% from peak).

**Two more calls resolved, and one of them matters.**
- **LINKUSDT stopped out** at 11.72 on a trailing stop (21:47). Entry 12.2401, so about −4.3%.
  This is the first real test of a same-day revision and it passed: the 7 Sep *morning* memo
  called LINK long 0.55; the 7 Sep *evening* memo cut it to flat on whale distribution and an
  RSI near 76. LINK went 13.455 → 12.764 → 12.47 → 11.706 and then through the stop. Had the
  long stood, it would have been wrong. The evening revision was the right call for the reason
  it gave.
- **AMZN sold** at 251.842 on a trend break (13:48), entry 258.639, about −2.6%. The 6 Sep memo
  was flat 0.55 on no catalyst before late October.

That makes four exits this week — ANZ.AX, AAPL, AMZN, LINKUSDT — every one a name the desk had
called flat. **The honest caveat: the desk has called flat on almost everything, and in a tape
that has fallen four days straight, flat is right by construction.** The claim worth testing is
not "flat calls were right" but "flats underperformed longs", and on that the record is bad so
far: both long calls are underwater. NVDA (long 0.62 on 6 Sep) is −3.0% and MSFT (long 0.55 on
6 Sep) is −1.7%. The desk's two directional bets have both lost money. That belongs in Sunday's
calibration table, not buried.

**Picks: 4.** Holdings with no memo: **XLE** and **XLV**, both bought today. Plus **MSFT** and
**SPY**, whose memos dated 6 Sep are exactly three days old and both of which now sit in front
of a dated binary. No new candidates: the book is at its 12-position cap, and AMD (+0.45) and
XLF (+0.44) could not be entered anyway.

| symbol | direction | conviction | note |
|---|---|---|---|
| XLE | **long** | 0.55 | Top score +0.70, 55-day high at RSI 62; crude +5% to $90 on Hormuz strikes; XOM+CVX 42.5% of fund |
| MSFT | long | 0.55 | Reaffirmed. Both 6 Sep invalidations intact; Azure guided +44–45% cc; score +0.55 → +0.57 |
| XLV | flat | 0.55 | RSI 28 pullback in an uptrend, but I could not find what caused it |
| SPY | flat | 0.62 | FOMC now literally a coin flip; August CPI lands 11 Sep, 48 hours out |

**Deferred holdings** (fresh memo, nothing material): NVDA (flat 0.55, 8 Sep), DBC (flat 0.60,
8 Sep), BTCUSDT (flat 0.55, 8 Sep), QQQ (flat 0.62, 7 Sep), ETHUSDT (flat 0.60), BNBUSDT
(flat 0.60), SOLUSDT (flat 0.55), BHP.AX (flat 0.50, +3.9% and the best performer we hold, but
the flat thesis — spot above two of three broker targets — is unchanged).

No `avoid` memo on any held position. `validate-memos`: 16 valid.

**Why XLE is a long when DBC is a flat.** Same macro view, different vehicle and different
entry. DBC is the futures strip at RSI 76; XLE is the majors' cash flow at RSI 62, with Exxon
and Chevron 42.5% of the fund and Chevron committing $7B in September to double Venezuelan
output. XLE also carries the highest systematic score in the book and led on Tuesday, +1.1%
while the indices fell. Both memos carry the same bear case and it is a real one: the EIA has
Brent averaging ~$85/b in 3Q26 and J.P. Morgan $86/$80/$78 through year end, all below spot,
and energy ETF outflows are reported as the largest since 2024 even as price leads. If that
premium unwinds, both calls are wrong together — which is a concentration this desk should
watch, not admire.

**Macro (once for the day).** The picture sharpened into a dated binary. Hike odds have fallen
from 57% to roughly 49–51%, so the 15–16 Sep FOMC is now a true coin flip between a 25bp hike
and a hold, and **August CPI on the morning of 11 September is the print that resolves it**.
The 10-year at 4.796% and the 2-year at 4.394%, the latter its highest since January 2025.
Crude spiked 5% to $90 on renewed Hormuz strikes, keeping the supply-side inflation impulse
alive. macro_conviction long: 0.35.

**Nothing failed today.** Last night's push race did not recur; the schema defect filed
yesterday (`us_etfs` missing from the memo enum) is still open and today added two more
`us_etfs` memos — XLE and XLV — that validate but violate the documented schema.

## 2026-09-10 — council run

Packet: `research/packets/2026-09-10.md`. Thursday. Equity 9,780.75 (fifth down session,
−2.9% from the 10,073 peak), 12 positions, cash down to 860.08.

**A thesis of mine looks wrong, and it is the one I was most confident about.**
The 7 Sep AAPL memo called flat 0.60 on the argument that "the base rate for owning Apple into
its own September event is the least favourable setup in large-cap tech". Day one supported it —
Apple dipped 1% on 9 Sep, against a five-year average of −0.72% on announcement day. The rest
does not: AAPL is 326.57 today, up from 315.34 on 9 Sep, and Bank of America's Wamsi Mohan finds
the stock has *gained* in the 60 days after an iPhone reveal in 17 separate instances going back
to 2007. I asserted a base rate without looking up the actual post-event statistics, and the
statistics point the other way. The desk rules say base rates first; I wrote the sentence and
skipped the work. Recording it as a research failure, not a market surprise.

**XLV: a one-day round trip, and the flat call was right.** Bought 9 Sep 21:48 at 166.66, sold
10 Sep 14:47 at 165.76 on a trend break. Yesterday's memo said flat because I could not identify
what caused the RSI-28 selloff and that it flips long only on "a reclaim, not a falling knife".
It kept falling — RSI 31, score +0.53 → +0.19.

Also exited: QQQ at 708.66 and SPY at 757.652, both trend breaks, both called flat by the desk.

**Picks: 8 (the cap).** Holdings with no memo: **AMD**, **CSL.AX**, **XLK**, all bought today.
Holdings whose memo turned three days old: **BHP.AX**, **ETHUSDT**, **SOLUSDT**, **BNBUSDT**.
Plus **XLE**, re-run because my own long deteriorated materially.

| symbol | direction | conviction | note |
|---|---|---|---|
| XLE | long | 0.50 | Held deliberately (was 0.55). Brent $101.25 and escalating, but score +0.70 → +0.47 |
| CSL.AX | flat | 0.65 | ~20% above the A$139.20 average target after +62.7%; FY26 underlying −2%, FY27 guides ~5% |
| XLK | flat | 0.60 | ~16% NVDA, ~45% top five — duplicates NVDA, AMD and MSFT; September is its weakest month |
| SOLUSDT | flat | 0.60 | Fell *through* its own SEC catalyst, $105 → $99.92, breaking the 103.35 level |
| BNBUSDT | flat | 0.60 | Worst position at −5.4%; no catalyst until the mid-Oct burn |
| AMD | flat | 0.55 | Real MI400 cycle but forecast revenue, +190% in a year, fourth overlapping AI bet |
| BHP.AX | flat | 0.55 | Iron ore firm at $100/t, but only ~30% of Chinese mills profitable vs 61% a year ago |
| ETHUSDT | flat | 0.55 | Slightly better: spot ETH ETFs +$34M on a day BTC saw outflows |

**Deferred** (fresh memo, direction unchanged): NVDA (flat 0.55, 8 Sep — now −5.3%, the worst US
position, but the call does not change), DBC (flat 0.60, 8 Sep — now +4.1% and top score +0.70),
BTCUSDT (flat 0.55, 8 Sep), MSFT (long 0.55, 9 Sep).

No `avoid` memo on any held position. `validate-memos`: 19 valid.

**Why XLE stayed long when NVDA and LINKUSDT were cut.** This is the third day running where a
long call came under pressure, and I want the rule to be legible rather than mood-driven. The
XLE memo named a concrete invalidation — a close below 62.00 — and price is 64.93, so the thesis
has not been falsified; meanwhile the *catalyst strengthened* (Brent $101.25, five Iranian
tankers destroyed, Houthi strikes on Saudi facilities). Cutting it today would mean my
invalidation levels are decoration and the memos are just a lagging echo of the systematic score.
So conviction came down 0.55 → 0.50 and the position stands.

The honest counter-argument is in the memo: yesterday I claimed XLE was a better vehicle than
DBC for this view, and in 24 hours DBC is +4.1% while XLE is −1.2%, with the scores swapping
places. Oil went up and the oil equities went down. I have written into the XLE invalidation
that if that divergence persists another week, the vehicle choice was wrong and it goes flat on
its own evidence rather than on a score wobble.

**Macro (once for the day).** Reversed hawkish inside 24 hours. CME FedWatch has a hike back at
**62.2%**, up from roughly 49–51% yesterday. PPI printed today and August CPI lands tomorrow
morning — the last inflation reads before the 15–16 Sep FOMC. Brent $101.25 after US forces
destroyed five Iranian tankers and Houthi militants struck Saudi energy facilities; Qatar and
China are trying to revive Hormuz diplomacy against that. Iron ore $100.02/t at six-week highs
on pre-holiday Chinese restocking, though only ~30% of Chinese steelmakers are profitable.
macro_conviction long: 0.30, down from 0.35.

**Nothing failed operationally.** The `us_etfs` schema defect filed on 8 Sep is still open and
today added two more memos against it (XLK, XLE).

## 2026-09-11 — council run

Packet: `research/packets/2026-09-11.md`. Friday. Equity 9,861.75, up 81 on the day after five
down sessions; 12 positions; **cash down to 25.42 — the book is fully invested.**

**August CPI decided the week.** Headline +0.4% m/m and 3.4% y/y, core +0.3% against a 0.2%
estimate, and gasoline up 3.9% accounting for over a third of the monthly increase. The
energy → inflation → Fed chain this desk has been describing since 6 September is now in the
data rather than in the argument. Hike odds for 15–16 Sep jumped: sources put them between ~69%
and 85–90%, and the spread between those two figures is itself worth noting — every source
agrees on direction, none agrees on magnitude. Equities rose anyway, Dow and Nasdaq +0.9%,
S&P +0.8%, ending a four-day losing streak but still down on the week. Oil fell on Friday.
macro_conviction long: 0.25, the lowest yet.

**Prior calls.** BHP.AX stopped out at 43.406 (entry 44.8744, about −3.3%); yesterday's memo was
flat 0.55 on Chinese mill profitability. That is a fifth exit on a name the desk had called flat.

**The AAPL miss got worse.** AAPL is 332.27 today with RSI 71, against 315.34 on event day —
about +5.4% since the exit. My 7 Sep sell-the-news thesis is now clearly wrong on every horizon
except day one, and the BofA 60-day base rate I failed to look up is the one that is playing out.

**Churn worth flagging: XLF was bought at 00:47 and sold at 02:47**, a two-hour round trip
(−0.25%), and the buy leg is marked `alpaca-paper skipped`, so the broker may not have filled
what the simulator recorded. Two hours is not a trend-following holding period. Worth the
owner's attention as an execution question, not a research one.

**Picks: 5.** Holding with no memo: **EEM**, bought at 02:47. Memos turned three days old:
**BTCUSDT**, **DBC**, **NVDA**. Plus **ETHUSDT**, re-run because its score jumped to +0.85 with a
55-day breakout — the largest single-day change in the book and the one name where my own long
trigger is now in play.

| symbol | direction | conviction | note |
|---|---|---|---|
| EEM | flat | 0.60 | Every EM bull case rests on a weaker dollar; we bought it the week the hike got priced |
| NVDA | flat | 0.60 | Five sessions of decay, −5.3%, muted on a +0.9% Nasdaq day |
| DBC | flat | 0.60 | Hedge vindicated by the CPI gasoline line, but score +0.70 → +0.50 |
| BTCUSDT | flat | 0.60 | Flows rotated to ETH; that was the reason to prefer BTC in this sleeve |
| ETHUSDT | flat | 0.50 | Flow trigger met decisively; price trigger not. See below |

**Deferred** (fresh memo, direction unchanged): MSFT (long 0.55, 9 Sep — the only long equity
call, score up to +0.62), XLE (long 0.50, 10 Sep), AMD, CSL.AX, XLK, SOLUSDT, BNBUSDT (all flat,
10 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**ETHUSDT and the discipline of not moving a trigger.** Yesterday's memo said ETH flips long on
"a daily close above 2,700 with two consecutive weeks of positive spot Ether ETF inflows". The
flow condition is now met emphatically — US spot Ether ETFs took their largest daily inflow since
October 2025 at $189.15M, $1.85B last month and +$106M so far in September — and the packet has
ETH at the top of the book, score +0.85 with a 55-day breakout. The price condition is not:
2,534.99 on our feed against a 2,700 trigger, and external desks report ETH consolidating at
$2,441 and repeatedly rejected at $2,550.

The tempting move is to lower the trigger to just above $2,550 and call it long. I have not,
and the memo says why: moving an invalidation toward spot after the evidence improves is how a
named level becomes decoration. $2,550 is flagged as the level the market is actually fighting
over and the early signal to watch, but the trigger stays at 2,700. Conviction came down 0.55 →
0.50 to reflect that I am closer to changing my mind, which is the honest way to express it.

Also worth recording: our feed says 2,534.99 and external reporting says $2,441 on the same day.
That is a wider gap than a timing difference explains, and it is the second time this week a
crypto mark has disagreed with outside quotes.

**Still open:** the `us_etfs` schema defect from 8 Sep. Today added two more memos against it
(EEM, DBC).

## 2026-09-12 — council run

Packet: `research/packets/2026-09-12.md`. **Saturday** — US and ASX did not trade, so every
equity mark is Friday's close and only crypto moved. Equity 9,848.99, 12 positions unchanged,
cash 25.42. No exits, no entries.

**The record, in one line:** nine closed trades, nine losses, −$97.25 realised, expectancy −2.08%
per trade, and the desk's own long memos are 2 good out of 4 judged — a coin flip, so conviction
on both longs today is set below where the evidence alone would put it.

Reading further into `research/outcomes.json`: exits are the weak link, not entries. Buy
decisions score 4 good out of 5 judged (0.80); **sell decisions score 0 out of 4 (0.00)**. Trades
entered with a flat memo lost −$23.33 across 5; trades with no memo at all lost −$73.91 across 4,
so having an opinion has been worth something even when the opinion was "no". Average hold is
2.4 days, which for a 55-day-breakout system is a mismatch worth the owner's attention.

**Picks: 2.** Only **MSFT** was strictly due (memo 9 Sep, three days). I added **XLE** because the
record instruction says be stingier when longs have been wrong, and these two are the only longs
on the desk — re-examining them is where that instruction bites. Everything else has a memo one
or two days old and, on a day the equity market was shut, nothing material changed.

| symbol | direction | conviction | note |
|---|---|---|---|
| MSFT | long | 0.50 (was 0.55) | Squeeze 0.69, 7.8% below the 52w high, score 0.55 → 0.62 on the week |
| XLE | long | 0.45 (was 0.50) | Brent +9% on the week to ~$104, but Gulf–Iran Hormuz talks land Monday |

**Deferred** (fresh memo, nothing material, market shut): AMD, CSL.AX, XLK, SOLUSDT, BNBUSDT
(all 10 Sep), BTCUSDT, DBC, NVDA, EEM, ETHUSDT (all 11 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The lesson that changed a call today:** the outcomes summary. Both longs kept their direction —
MSFT's own evidence improved all week and XLE's named invalidations have not fired — but both had
conviction cut a notch purely on the 2-for-4 long record. That is the record changing the number
rather than the verdict, which is the honest use of it.

**A correction to my own framing.** On 10 September I wrote that if the DBC/XLE divergence
persisted "another week" with XLE lagging a rising Brent, the vehicle choice was wrong. Brent rose
9% this week while XLE fell 0.9%, and my first instinct today was to call that condition met. It
is not: I said a week, and it has been two days. The date that test falls due is **17 September**
and it is written into today's XLE invalidation. Acting early on a condition I set myself would be
exactly the goalpost-moving I refused on ETHUSDT yesterday, in the other direction.

Worth noting honestly on the same point: the packet's `rs` column is empty, but relative strength
is derivable from the table, and it does not support the "XLE is lagging" story on a quarter view —
XLE's 63d momentum of +14.9% leads SPY's +3.9% by about 11 points, and DBC's 63d momentum is also
+14.9%, identical. The divergence is real over three sessions and absent over three months.

**Macro (once for the day).** The FOMC on 15–16 September is close to decided: prediction markets
price a 25bp hike at 79.5%, one tracker reached ~90% after CPI, up from 70% on Thursday.
EY-Parthenon moved from hold to a 25bp hike taking the range to 3.75–4.00%; Capital Economics
projects a second hike in December and a third in March 2027. Brent settled near $104, up 9% on
the week, then paused as Iran agreed to meet Gulf states in Oman; GCC diplomats meet their Iranian
counterpart **Monday** on a temporary Hormuz shipping arrangement. Against that, the IEA sharply
cut its demand outlook to a 2.5 mb/d contraction in 2026 and the EIA raised 2027 US production to
14.3 mb/d. macro_conviction long: 0.25.

**Things that failed or need checking.**
- The routine says the packet has "a section listing the event and news gates in force". Today's
  packet has no such section — its headings are Account, Open positions, Candidates, Full signal
  table, Headlines, Memo schema. Either the gates did not render or the routine is ahead of the
  generator.
- The `rs` column exists in the signal table header and is `-` for all 49 symbols. The pattern
  analyst prompt names rs as an input it should use, so it is currently working blind on relative
  strength unless it derives the number itself, which I did by hand today.
- Minor: our MSFT mark is 495.63 against an external report of $493.87 for Friday's close.
- Still open since 8 Sep: `us_etfs` missing from the memo schema enum. Today's XLE memo is the
  seventh written against it.

## 2026-09-13 — council run + weekly review

Packet: `research/packets/2026-09-13.md`. **Sunday** — equity marks are Friday's close again, only
crypto moved. Equity 9,838.79, same 12 positions, cash 25.42, no exits and no entries all weekend.

**The record, in one line:** nine closed trades, nine losses, −$97.25 realised, expectancy −2.08%
per trade, long memos 2 good of 4 judged — so conviction stays capped and nothing today is above
0.6.

**Picks: 6.** Memos turned three days old for **AMD**, **BNBUSDT**, **CSL.AX**, **SOLUSDT** and
**XLK**. Plus **XLE**, re-run one day early on a material change.

| symbol | direction | conviction | note |
|---|---|---|---|
| XLE | flat | 0.55 | **Cut from long 0.45.** Muscat signing on a Hormuz shipping route is tomorrow |
| XLK | flat | 0.60 | Derived rs shows it *lagging* SPY by 1.3pts while holding the biggest tech names |
| SOLUSDT | flat | 0.60 | Still below 103.35; CLARITY Act vote 15th, FOMC 16th |
| BNBUSDT | flat | 0.60 | Worst position at −4.3%; squeeze 1.14, volatility expanding on a falling price |
| AMD | flat | 0.55 | Targets raised to $600–635 while score fell 0.46 → 0.41 and momentum halved |
| CSL.AX | flat | 0.50 | Conviction cut — my own valuation anchor turned out to be contested |

**Deferred** (memo one or two days old, nothing material): MSFT (long 0.50, 12 Sep — now the only
long on the desk), BTCUSDT, DBC, NVDA, EEM, ETHUSDT (all 11 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The statistic that changed a call today:** `by_memo_at_entry` in `research/outcomes.json`.
Trades entered with a flat memo lost **−$4.67 each**; trades entered with no memo lost **−$18.48
each**. That is the first sign the research layer carries information, and it is why I did not
treat today's run as busywork on a weekend when nothing traded.

**Cutting XLE, and why this is not the whipsaw it looks like.** Yesterday I held XLE long and
argued that re-rating before a named condition fires makes invalidation levels decoration. Today I
cut it to flat. The difference is the fact, not my mood: yesterday the report was that Gulf and
Iranian officials would *meet* about Hormuz; today CNN reports they meet in Muscat on Monday **to
sign** an agreement establishing an Iran-Oman shipping route. Both prior XLE memos named a
reopening of Hormuz transits as an immediate invalidation. A signing is still not a reopening —
a vessel was struck in the Strait today, the US is excluded from the talks and the naval blockade
stands — so the thesis is not dead and the position is not sold; the stop at 62.85 governs. But
"long" means worth owning now, and that cannot be defended into a binary I called fatal, with
£0 of spare cash to react.

**Two corrections to my own earlier memos.**
1. **CSL.AX valuation anchor.** On 10 September I wrote that CSL was ~20% above an A$139.20 average
   analyst target, and that claim carried the whole flat 0.65 call. Today's sources put Macquarie
   at A$188 (cut from A$275) and a fair value of A$210.90 (trimmed from A$228.58) — which would
   make A$167.10 a *discount*. I cannot reconcile the two secondary summaries, so today's memo
   treats valuation as unknown and rests on the business record instead: four major guidance cuts
   in two years. Conviction 0.65 → 0.50.
2. **AAPL**, recorded again for the calibration trail: now ~332 against the 315.50 exit, so the
   sell-the-news thesis is wrong on every horizon except day one.

**Weekly review** written to `research/reviews/2026-09-13-review.md`, citing this week's
`study-2026-09-12.md` and `wf-2026-09-12.md`. Both say keep the live parameters and both deserve
belief on that: re-picking each window returned +84.2% against +112.6% for holding. Three findings
worth carrying forward:
- **Exits are the broken part, not entries.** Buy decisions score 4 good of 5 (0.80); **sell
  decisions score 0 of 4 (0.00)**. Seven trend-break exits cost −$54.44.
- **Hold period and signal are mismatched**: a 55-day-breakout system with a 2.4-day average hold,
  including two same-day round trips (XLV, XLF).
- **No memo above 0.7 conviction has been written in eight days**, so the high band is untested.

New proposal filed: `research/proposals/2026-09-13-populate-rs.md`. The `rs` column has been empty
for three straight days while this week's study ranks `+rs 0.15` **first of ten variants** by
robustness (0.79 against live 0.53). The desk cannot see the one signal its own research ranks
highest. Also noted: `n8` tops the 97-variant report again, the second week running, which is the
subject of the still-untested 7 September proposal.

**Things that failed or need checking.**
- Third day with no event/news gates section in the packet, though the routine describes one.
- Third day with `rs` empty for all 49 symbols.
- `us_etfs` still missing from the memo schema enum (open since 8 Sep; two more memos today).
- Feed drift again: our SOL 101.40 against $99.31 externally, BNB 722.38 against $710–714.

## 2026-09-14 — council run

Packet: `research/packets/2026-09-14.md`. Monday. Equity 9,806.30, 12 positions, **cash 0.00**.

**The record, in one line:** eleven closed trades, eleven losses, −$148.09 realised, expectancy
−2.84% per trade, and long memos are now **3 good of 7 judged (0.43)** — below a coin flip — so
nothing today is written above 0.65.

**My first long memo the engine acted on has been stopped out.** NVDA exited at −8.48% (−$10.37),
eight days held. I called it long 0.62 on 6 September on a 55-day breakout, downgraded to flat on
8 September when that breakout failed, and the position ran to the stop anyway. The `long` row now
appears in `by_memo_at_entry` for the first time: n=1, −$10.37. **AMD** also exited, −4.04%
(−$40.48) — the second-largest single loss on the book — on a name the desk called flat twice.
Flat was right in the sense of "do not add" and still cost $40 because the engine held it.

**Picks: 6.** Memos turned three days old for **BTCUSDT**, **DBC**, **EEM** and **ETHUSDT**. Plus
**AAPL** and **LINKUSDT**, both re-entered by the engine today and both carrying memos a week old.

| symbol | direction | conviction | note |
|---|---|---|---|
| EEM | flat | 0.65 | Momentum flipped +1.0% → −2.3%, lowest score in the book, stop 1.7% away |
| AAPL | flat | 0.60 | BofA ship times *shorter* than last year — 14d vs 18d Pro, 18d vs 25d Pro Max |
| BTCUSDT | flat | 0.60 | Funds bled $463M last week while ether took $197M |
| DBC | flat | 0.60 | Iran-Oman agreed a temporary route; RSI 75 within 1.4% of the high |
| LINKUSDT | flat | 0.55 | Re-bought five days after costing $37.45; squeeze 1.31, ATR 5.9% |
| ETHUSDT | flat | 0.45 | Nearly persuaded — see below |

**Deferred** (memo one or two days old, nothing material): MSFT (long 0.50, 12 Sep — the only long
on the desk, now +1.1% and score up to +0.65), XLE, CSL.AX, XLK, SOLUSDT, BNBUSDT (all 13 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The statistic that changed a call today:** long memos falling to 3-of-7. That is what kept
ETHUSDT flat. Ether took **$197M of ETF inflows last week while bitcoin funds bled $463M**, it
holds the top score in the book at +0.85 with a 55-day breakout, RSI 57 and 24.2% of headroom below
its 52-week high — the cleanest structure I have seen since this desk started. My trigger was a
close above 2,700 and price is 2,548, sitting on the $2,550 ceiling that has rejected it
repeatedly. Conviction goes to **0.45** to record that I am nearly persuaded. The trigger stays at
2,700 for the third day running. If it breaks 2,700 and I then call it long, that call will have
been earned rather than chased.

**A correction I owe the record: my AAPL thesis was wrong on direction.** The 7 September memo
called flat 0.60 arguing sell-the-news; AAPL went from a 315.50 exit to 333 and now sits 2.0%
below its 52-week high. The engine has just re-bought it at 332.49. Today's memo is still flat but
on entirely different evidence — Bank of America's ship-time tracking, the first hard demand data
of this cycle, shows iPhone 18 Pro waits at 14 days against 18 for the 17 Pro a year ago and Pro
Max at 18 against 25. Shorter queues mean a thinner order book. Being right for a new reason is
not the same as having been right.

**Hormuz: my named invalidation did not fire, precisely.** Iran and Oman agreed a shipping route,
but it is a **temporary** route running two to four months and explicitly not a full reopening of
the Strait. Yesterday's XLE memo cut to flat ahead of this and that call stands; the thesis is not
dead and XLE keeps its 62.85 stop. Recorded because the distinction between "a route agreed" and
"the Strait reopened" is exactly the kind of thing a desk talks itself out of after the fact.

**Macro (once for the day).** The FOMC decides Wednesday and the odds are genuinely contested —
Kalshi showed 48% for a 25bp hike while another tracker had 83%, so the week's most consequential
number is one nobody agrees on. The CLARITY Act reaches a Senate vote tomorrow on a revised bill
with White House-backed ethics concessions; analysts describe it as simultaneously dead and alive
until the vote. macro_conviction long: 0.25.

**Things that failed or need checking.**
- Fourth day with no event/news gates section in the packet, though the routine describes one.
- Fourth day with `rs` empty for all symbols — proposal filed yesterday.
- `us_etfs` still missing from the memo schema enum (open since 8 Sep).
- **Cash is 0.00 and the book is at its 12-position cap.** Every call this desk makes is now
  advisory only: there is no capital to act on a "long" and no slot to take a new idea. Worth the
  owner's attention — it is the context for every conviction number above.

## 2026-09-15 — council run

Packet: `research/packets/2026-09-15.md`. Tuesday. Equity 9,656.55, 12 positions, cash 0.00.
Crypto fell 4–8% across the sleeve: SOL −7.8%, BNB −5.5%, BTC −3.9%, ETH −3.9%, LINK −4.4%.

**The record, in one line:** twelve closed trades, twelve losses, −$168.00 realised — and long
memos now read 6 good of 7 judged (0.86), against 3 of 7 (0.43) yesterday. **A hit rate that
halves and doubles overnight on seven judged memos is noise, and I am not treating it as licence
to get bolder.** Skip decisions are 20 of 20.

**EEM stopped out at −1.94% (−$19.90).** Yesterday's memo was flat 0.65 and said in terms that the
stop sat 1.7% below spot and this was close to being resolved by the risk engine rather than by
research. It was, within a day.

**Picks: 7.** Due: **MSFT** (memo three days old) and **XLV** (re-entered today, memo a week old).
Re-run on material change: **XLE** and **CSL.AX** (both printed fresh 55-day highs, scores to +0.75
and +0.85), **DBC** (packet now flags it overbought at RSI 87), **ETHUSDT** (score +0.85 → +0.62
after a failed breakout) and **SOLUSDT** (−7.8%, the worst position on the book).

| symbol | direction | conviction | note |
|---|---|---|---|
| MSFT | long | 0.50 | Unchanged fourth run; squeeze 0.73, leads SPY by ~24 points, both invalidations intact |
| DBC | flat | 0.65 | RSI **87** — above the engine's own 80 entry-refusal line |
| SOLUSDT | flat | 0.60 | Below both the 103.35 level and its pre-catalyst price; stop 6% away |
| XLV | flat | 0.60 | Re-bought at RSI 29, five days after the same trade lost money at RSI 28 |
| ETHUSDT | flat | 0.55 | Failed breakout; the 2,700 trigger held and today is why |
| XLE | flat | 0.50 | Fresh 55-day high but RSI 74 at the literal 52-week high |
| CSL.AX | flat | 0.50 | Top score +0.85, best structure in the book — flat by 74 cents |

**Deferred** (fresh memo, direction unchanged): AAPL, LINKUSDT, BTCUSDT (14 Sep), XLK, BNBUSDT
(13 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The statistic that changed a call today: none.** The long-memo hit rate moved violently in my
favour and I deliberately ignored it — with seven judged memos, that number is not yet information.
What decided today's calls was price structure.

**Holding the ETH trigger was right, and this is the cleanest evidence the desk has produced.**
Yesterday ETH had the top score in the book at +0.85, a 55-day breakout, RSI 57, 24% of headroom,
and the best flows in crypto — $197M of ETF inflows while bitcoin bled $463M. I wrote that I was
nearly persuaded, cut conviction to 0.45 to say so, and refused to lower the 2,700 trigger toward a
spot price of 2,548 sitting on the $2,550 ceiling. Today ETH is 2,401, the breakout has failed, the
score is +0.62 and the squeeze has flipped to 1.04. Not lowering a trigger to meet a price is worth
roughly 6% on this one occasion.

**An admission on XLE.** Cutting it from long to flat on 13 September was premature in outcome. The
Muscat signing produced only a temporary two-to-four-month route, the disruption never eased, and
XLE has since gone 64.53 → 65.93 to sit at its 52-week high with the second-highest score in the
book. Brent is ~$107.5, a four-month high, with Saudi Arabia's East-West pipeline offline after
attacks and repairs possibly taking weeks. Had the long stood, it would have been right. It is
still flat today, because RSI 74 at the literal 52-week high is not an entry and I applied exactly
that rule to DBC at RSI 75 yesterday — applying it to one energy holding and not the other would be
arbitrary. Recording both halves: the call was wrong, and the rule that produced it is still right.

**CSL.AX resolves last week's confusion.** On 13 September I could not reconcile an A$139.20 target
with A$188–211 figures and flagged it as a research failure. It was not: broker targets on CSL
genuinely run from **A$131.49 to A$206.76**, a 57% spread, and the trade press headline is that
brokers cannot agree what happens next after a 90% run off the June low. The dispersion *is* the
finding. Valuation supports neither side, so the memo rests on the business record instead. It
stays flat by the narrowest margin yet: my trigger was a close above A$175 native **and** a broker
raising; it closed A$174.26 and I found no upgrade.

**Macro (once for the day).** The FOMC decides tomorrow. Today's CLARITY Act vote was **cloture
only** — a 60-vote threshold merely to begin debate, which even if cleared does not pass the bill;
the crypto sleeve appears to have been positioned for more than the vote could deliver. Brent
~$107.5, a four-month high, on the Saudi pipeline outage, with Iran refusing to negotiate until
its conditions are met. macro_conviction long: 0.25.

**Things that failed or need checking.**
- Fifth day with no event/news gates section in the packet, though the routine describes one.
- Fifth day with `rs` empty for all symbols — derived by hand again today.
- `us_etfs` still missing from the memo schema enum (open since 8 Sep; four more memos today).
- Cash 0.00 for a second day with the book at its 12-position cap: every call remains advisory.

## 2026-09-16 — council run

Packet: `research/packets/2026-09-16.md`. Wednesday. Equity 9,628.71, same 12 positions, cash 0.00.

**The Fed hiked.** 12-0 for 25bp to 3.75–4.00%, the first increase since July 2023, with Warsh
promising a "timelier return" to 2%. The dot plot is the part that matters: **16 of 18 participants
expect another increase and four see two more**. Dow −631 (−1.21%) to 51,461.90, S&P 500 −0.45% to
7,551.81, Nasdaq flat, and the 10-year yield eased about 5bp to 4.947%. The macro overhang this
desk has cited since 6 September is now resolved, hawkishly, with more signalled.

**The record, in one line:** twelve closed trades, twelve losses, −$168.00 — and long memos read
3 good of 8 (0.375) today after 6 of 7 (0.86) yesterday and 3 of 7 (0.43) on Monday. Three
different answers in three days; I said yesterday that number was noise and today confirms it in
the other direction, so it is steering nothing. Skip decisions are 17 of 17.

**Picks: 5.** Due: **BNBUSDT** and **XLK** (memos three days old). Re-run on material change:
**XLE** (−2.6%, score +0.75 → +0.52, RSI 74 → 58), **MSFT** (the only long, −1.9% into the hike)
and **DBC** (RSI 87 → 77).

| symbol | direction | conviction | note |
|---|---|---|---|
| MSFT | long | 0.45 | Cut from 0.50 — the hike was priced, another one was not |
| DBC | flat | 0.60 | RSI unwound 87 → 77 without giving back the gain |
| XLK | flat | 0.60 | 63-day momentum now **negative** at −1.2%, lowest score in the book |
| BNBUSDT | flat | 0.60 | Stop 3% away; squeeze 1.19, volatility expanding on a falling price |
| XLE | flat | 0.50 | **My own long trigger is met and I am declining it** — see below |

**Deferred** (fresh memo, direction unchanged): CSL.AX, SOLUSDT, ETHUSDT, XLV (15 Sep), AAPL,
LINKUSDT, BTCUSDT (14 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The statistic that changed a call today:** none from the record. The Fed's dot plot changed two
calls — MSFT down a notch and XLE held flat.

**XLE: declining a trigger I wrote, and saying so.** Yesterday's memo said XLE flips long on "a
pullback that holds above 63.50 with Brent still above $100". The pullback arrived inside 24 hours:
price 64.03, RSI down from 74 to 58, Brent about $108. As written, the condition is met. I am not
taking it, because today produced evidence the trigger was never drafted to capture — a 25bp hike
with 16 of 18 officials wanting more, aimed squarely at the demand side of an energy trade, plus a
US industry report showing stockpiles rising and the supply rally judged overdone after a 4%
two-session run.

Two things follow, and both belong on the record. First, this is the mirror image of Monday's ETH
decision: there I refused to *lower* a trigger toward price, here I am refusing to *act* on one
that price reached. The common rule is that the trigger is a floor for acting, not a substitute for
judgment when new facts arrive — but I want that stated plainly rather than discovered later.
Second, "a pullback that holds" was sloppy drafting: it has no session count, so it turned a test
into an argument. Today's XLE memo replaces it with **three consecutive closes above 63.50**.

**Yesterday's XLE call was right for the reason given.** I held it flat at RSI 74 on the 52-week
high, said the entry was poor and to wait for a pullback, and it fell 2.6% the next session. That
is the second consecutive day a refusal to chase an extended reading has paid — ETH on Monday,
XLE today.

**Things that failed or need checking.**
- Sixth day with no event/news gates section in the packet, though the routine describes one.
- Sixth day with `rs` empty for all symbols; derived by hand again (XLE +16 points over SPY, MSFT
  +24, XLK −2).
- `us_etfs` still missing from the memo schema enum (open since 8 Sep; three more memos today).
- Cash 0.00 for a third day at the 12-position cap: every call remains advisory, including the XLE
  trigger debated above, which could not have been acted on either way.

## 2026-09-17 — council run

Packet: `research/packets/2026-09-17.md`. Thursday. Equity 9,782.26, up $153 on the day; same 12
positions; cash 0.00.

**The record, in one line:** twelve closed trades, twelve losses, −$168.00 — and the long-memo hit
rate has now printed **0.43, 0.86, 0.375, 0.625 on four consecutive days** as past memos get
re-judged. Four different answers in four days is not a signal, so it steered nothing today; the
skip hit rate did the same thing, 1.00 yesterday and 0.33 today.

**Picks: 4.** Due (memos three days old): **AAPL**, **BTCUSDT**, **LINKUSDT**. Plus **CSL.AX**,
re-run because its trigger fired.

| symbol | direction | conviction | note |
|---|---|---|---|
| CSL.AX | **long** | 0.55 | **Both legs of the 15 Sep trigger fired** — see below |
| AAPL | flat | 0.65 | A second bank, JPMorgan, now confirms shorter ship times than last year |
| BTCUSDT | flat | 0.60 | RSI 30, but $746M of ETF outflows in two sessions with zero inflow days |
| LINKUSDT | flat | 0.55 | My whale bear case was half the picture — see below |

**Deferred** (fresh memo, direction unchanged): MSFT (long 0.45, 16 Sep — now +0.65 score and
−0.4%), XLE, DBC, XLK, BNBUSDT (16 Sep), SOLUSDT, ETHUSDT, XLV (15 Sep).

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**The first trigger this desk wrote in advance has fired on both legs.** On 15 September I said
CSL.AX flips long on a close above A$175 native **and** at least one broker raising rather than
trimming. Today it closed **A$177.56** and **RBC Capital Markets upgraded CSL to buy, lifting its
12-month target from A$148 to A$213**. RBC's reasoning answers the objection I have carried since
10 September — that flat FY27 revenue and ~5% profit growth cannot support a 59% quarter — by
putting a mechanism under it: Behring growth offsetting weak Seqirus and Vifor, mid-single-digit
EPS growth for three years, A$1.5B of annual buybacks to FY31. The structure is the best in the
book: fresh 55-day high, 17.4% of headroom below the 52-week high, RSI 65, squeeze 0.67.

Conviction is 0.55 rather than higher for a reason worth stating: RBC was at A$148 until this
morning. A house that moves its target A$65 in one step was recently badly wrong by its own
admission, and its A$213 widens the broker range to A$131–213 rather than settling it. One
upgrade adds a voice; it does not create a consensus.

**A bear case of mine was half the picture, and I want that on the record.** Since 7 September I
have cited a whale sending 2.41M LINK (~$26M) to Coinbase as evidence of distribution — it was in
five memos. That is real, but whales also **accumulated roughly 10.36M LINK (~$120M) after the 17%
correction**, about five times larger in the opposite direction. I was quoting one side of a
two-sided flow because the sell side was the side I found first. LINK stays flat on volatility
grounds — squeeze 1.33, the highest in the book, ATR 6.0% putting the stop 14% below spot — not on
the whale argument, which no longer supports the weight I put on it.

**AAPL: the evidence hardened.** On 14 September I flagged Bank of America's ship-time tracking as
the first hard demand data. JPMorgan now reports the same thing independently — seven days for the
Pro against 15 last year, 19 for the Pro Max against 24 — and GF Securities calls the preorders
lukewarm on limited upgrades against a $100 price rise. Two banks tracking separately is what turns
a datapoint into evidence, and conviction goes to 0.65. Retail availability starts tomorrow.

**Macro (once for the day).** The hike is done — 25bp to 3.75–4.00% on 16 September, 12-0, with 16
of 18 officials expecting another. The clearest transmission is in crypto: spot bitcoin ETFs shed
about $746M across the two sessions around the decision ($450.33M Tuesday, $295.98M Wednesday), the
largest daily outflow in over two months, led by IBIT at $144.11M, with zero inflow days this week.
Equities took it better — the book gained $153 on the day. macro_conviction long: 0.30.

**Things that failed or need checking.**
- Seventh day with no event/news gates section in the packet, though the routine describes one.
- Seventh day with `rs` empty for all symbols; derived by hand again (CSL not derivable — no ASX
  benchmark in the table; AAPL +11 points over SPY).
- `us_etfs` still missing from the memo schema enum (open since 8 Sep).
- Cash 0.00 for a fourth day at the 12-position cap. Today's CSL long is the sharpest illustration
  yet: a trigger fired exactly as designed and there is no capital to act on it — the call can only
  discourage the engine from selling, never add.

## 2026-09-18 — council run

Packet: `research/packets/2026-09-18.md`. Friday. **Equity 10,081.57, up $299 (+3.1%) on the day
and back above 10,000 for the first time since 8 September.** Same 12 positions, cash 0.00.

**The record, in one line, and it is not flattering:** twelve closed trades, twelve losses,
−$168.00; long memos 4 good of 10 (0.40); and the **skip hit rate has collapsed to 0.083 (1 of 12
judged)**. Unlike the earlier wild swings I dismissed as noise, that one is real information — the
desk was flat on its largest sleeve while the sleeve ran.

**The honest accounting: the crypto sleeve rallied and the desk was on the wrong side of all of
it.** LINKUSDT +8.5%, SOLUSDT +7.7%, ETHUSDT +5.2%, BTCUSDT +3.2%, BNBUSDT +1.3% — and every one
of those carried a flat memo. Measured from where I wrote them: SOL +16.9% since 15 September,
ETH +9.5%, LINK +9.3% in a day, BTC +6.1%.

One qualifier that is true and that I will not hide behind: **cash has been 0.00 for five days, so
every flat call was advisory.** The book held all five positions throughout and captured the whole
move — the equity gain proves it. A "flat" meant do not add, and there was nothing to add with. The
foregone return is theoretical. The judgment was still wrong.

**Picks: 5.** Due (memos three days old): **SOLUSDT**, **ETHUSDT**, **XLV**. Re-run on material
moves against yesterday's calls: **LINKUSDT** and **BTCUSDT**.

| symbol | direction | conviction | note |
|---|---|---|---|
| SOLUSDT | **long** | 0.50 | Upgraded from flat 0.60 — three dated catalysts, see below |
| ETHUSDT | flat | 0.55 | 2,627.62 against the 2,700 trigger, held for a fifth day |
| LINKUSDT | flat | 0.55 | Price leg met (12.40 > 11.86), squeeze leg not (1.26 > 1.0) |
| BTCUSDT | flat | 0.55 | Price leg met (81,176 > 79,661), flow leg not — zero inflow days |
| XLV | flat | 0.55 | RSI leg met (41 > 40), price leg not (168.39 < 170) |

**Deferred** (fresh memo, direction unchanged): MSFT (long 0.45), CSL.AX (long 0.55), AAPL, XLE,
DBC, XLK, BNBUSDT.

No `avoid` memo on any held position. `validate-memos`: 20 valid.

**SOLUSDT upgraded to long — the reasoning, since I refused four similar-looking setups this week.**
Three dated catalysts landed today: the **SEC granted Solana a five-year "Innovation Exemption" for
tokenized securities trading**; the mainnet cut target slot time from 300ms to 250ms at epoch 1037;
and Nasdaq-listed DeFi Development Corp took its treasury to 2.39M SOL (~$253M) with a $300M ATM
facility to buy more. Crucially the structure is the *opposite* of what I have been declining: RSI
63 with 22.9% of headroom below the 52-week high, where XLE was RSI 74 at its high and DBC RSI 87.
None of the extended tests fire. Conviction is capped at 0.50 because a large part of the day was
forced short covering — $170–230M of one-hour liquidations — and the crypto sleeve's own backtest
win rate is 17%.

**Four of today's five memos sit on triggers that are exactly half met**, which is either good
discipline or an elaborate way of never committing. Stated plainly so it can be judged later: ETH
is 2.8% below its level, LINK has the price but not the volatility condition, BTC has the price but
zero inflow days, XLV has the RSI but not the price. Each second leg exists for a reason I wrote
down in advance, and refusing to lower the ETH trigger was worth ~6% when it fell to 2,401 on
15 September. But if these legs are still unmet in a week while the positions run, the honest
conclusion will be that my conditions are drawn too tight, not that the market is wrong.

**Macro (once for the day).** The **CLARITY Act cloture vote failed** and crypto rallied regardless
— bitcoin reclaimed $80,000 on short liquidations of $170–230M an hour — which says the sector was
positioned for the bill to fail. This follows the Fed's 25bp hike to 3.75–4.00% with 16 of 18
officials expecting another. macro_conviction long: 0.35.

**Things that failed or need checking.**
- Eighth day with no event/news gates section in the packet, though the routine describes one.
- Eighth day with `rs` empty for all symbols; derived by hand (XLV +11 points over SPY).
- `us_etfs` still missing from the memo schema enum (open since 8 Sep).
- Cash 0.00 for a fifth day at the 12-position cap — the reason today's misses cost nothing real,
  and the reason today's SOL long cannot be acted on either.
- One source put XLV at $154.57 against our 168.39; I did not use the figure and cannot reconcile it.

## 2026-09-19 — viability review (owner instruction: earn or shut down)

No council run today. The owner asked directly whether this desk earns enough to justify running,
and that question is worth more than a fourteenth set of memos. Full working in
`research/viability.md`.

**A correction I owe, and it is a bad one.** I have written in this log repeatedly — 6, 13 and
14 September — that research "cannot change a decision" and that every call is "advisory only".
That was true on 6 September. It has been **wrong since the engine was wired up**:
`kismat/engine.py:38` sets `RESEARCH_WEIGHT = 0.4`, so memos carry **40%** of the combined score,
and 263 decisions in the journal show `combined != systematic`. I asserted the limitation once,
then repeated it for two weeks without re-reading the code. That is the same failure as the AAPL
base rate on 7 September: stating something load-bearing without checking it.

**What the desk has actually done to the book: nothing measurable.** Having the power did not mean
using it. No entry was ever pushed below the 0.35 threshold by a memo; all 12 sells were trend
breaks or trailing stops; no rotation fired on a research score. Measurable P&L impact over 13
days: **zero**.

**The mechanism I did not know until today: a `flat` memo scores exactly 0.0** — the conviction
number is discarded (`kismat/research/memos.py:58`). Flat is not neutrality; it is a **40% haircut**
on the systematic score. Writing *no memo* is the neutral act. About 80% of the 69 memos written
are flat, so for two weeks I have been applying a 40% penalty and describing it as "no edge here".

**The economics.** Opus 5 at $5/$25 per MTok, ~12 requests a day each re-sending a two-week
transcript, is roughly **$4/day → $90–240/month**. On a $10,081 account that is **11–29% a year**
just to run the desk, against a strategy whose own five-year walk-forward shows **+15.8% CAGR**.
The desk costs about what the strategy is expected to make. Account flat over 13 days: 10,064.06 →
10,057.26.

**Recommendation: weekly cadence + fresh session per run** (the daily trigger currently re-sends
this whole transcript on every call), implement the four findings the desk has actually produced —
exits are the broken half, `n8` over `n12`, populate `rs`, flat-memo penalty — and re-judge in a
month against a stated bar. If those are not implemented, shut it down: a desk nobody acts on is a
pure cost regardless of memo quality. Daily Opus only makes sense above roughly $100k of account.

**Not recommended: a live account yet.** Twelve closed trades, zero wins, no demonstrated edge from
the research layer.
