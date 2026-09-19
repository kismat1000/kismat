# Can this desk pay for itself? — 2026-09-19

Written in response to a direct instruction: earn enough to cover the cost of running, or be shut
down. This is the honest answer, with the arithmetic shown so it can be checked and corrected.

## 1. What the account has actually done

| | |
|---|---|
| Equity 6 Sep (after funding) | 10,064.06 |
| Equity 19 Sep | 10,057.26 |
| **Net, 13 days** | **−$6.80 (−0.07%)** |
| Realised | −$168.00 across 12 closed trades, **0 wins** |
| Unrealised (12 open) | +$233.33 |
| Cash | 0.00, book at its 12-position cap |

The account is flat. Realised losses are being offset by open positions that have not been closed
yet, which is not the same as being profitable.

## 2. What the desk has actually contributed: nothing measurable

I have been reporting for two weeks that research "cannot change a decision". **That was true on
6 September and it is wrong now, and I should have re-checked it.** The engine wires research in at
`RESEARCH_WEIGHT = 0.4` (`kismat/engine.py:38`) — memos carry **40%** of the combined score — and
263 decisions in the journal show `combined != systematic`. The desk has real power.

It has not used it to any measurable effect:

- **No entry was ever blocked.** Checking every `skip` where research dragged the score: zero cases
  where a systematic score above the 0.35 entry threshold was pushed below it. The systematic
  scores (0.6–0.85) were high enough to survive the haircut.
- **No exit was ever driven by research.** All 12 sells were trend breaks or trailing stops.
  `exit_score_threshold` is −0.10 and combined never came close.
- **No rotation fired on a research score.**

So the desk's measurable P&L impact over 13 days is **zero**. It has neither earned nor cost
anything through the engine.

One mechanism worth knowing, because I did not know it until today: **a `flat` memo scores exactly
0.0** (`kismat/research/memos.py:58` — `sign = {"long": 1.0, "avoid": −1.0, "flat": 0.0}`), so its
conviction number is *discarded entirely*. A flat memo is not "no opinion" — it applies a **40%
haircut** to the systematic score. Writing no memo at all (`research = None`) is the genuinely
neutral act. Roughly 80% of the 69 memos written are flat. I have been applying a 40% penalty and
calling it neutrality.

## 3. What the desk costs

I cannot read my own billing from here, so this is an estimate with the arithmetic exposed —
replace it with real usage data if you have it.

Claude Opus 5: **$5.00/MTok input, $25.00/MTok output**, cache reads ≈ $0.50/MTok, cache writes ≈
$6.25/MTok. A daily council run is roughly 10–14 API requests (searches, file reads, memo writes),
and **each request re-sends the whole conversation** — this session now carries 13 days of
transcript.

| component | per daily run | cost |
|---|---|---|
| cache reads (~12 requests × ~350k ctx) | ~4.2M tok | ~$2.10 |
| fresh input (packet, search results) | ~80k tok | ~$0.40 |
| cache writes | ~100k tok | ~$0.63 |
| output + thinking | ~40k tok | ~$1.00 |
| **total** | | **≈ $4/day** |

Call it **$3–8/day → $90–240/month → $1,100–2,900/year**.

## 4. The number that decides it

On a **$10,081** account, $90–240/month is **0.9%–2.4% of the account per month**, or
**11%–29% per year**, purely to run the desk.

The system's own five-year walk-forward (`research/backtests/wf-2026-09-12.md`) puts the live
parameter set at **+15.8% CAGR**.

**The desk costs roughly what the strategy is expected to make.** At this account size the research
layer consumes the entire expected return before the owner sees a dollar. That is not a judgment
about research quality — it is arithmetic, and no amount of better memo-writing fixes it.

## 5. What would have to be true

**By account size.** For the desk to be ≤10% of expected profit at a 15.8% CAGR and ~$2,000/year
cost, you need ~$20,000/year of profit — a **~$127,000 account**. At a more conservative 10%
return, **~$200,000**. Below roughly $100k, a daily Opus desk cannot be justified on any
assumption I can defend.

**By cost, at the current size.** Four levers, cheapest first:

1. **Fresh session per run** (biggest free win). The daily Routine currently fires into *this*
   session, re-sending two weeks of transcript on every call. A `create_new_session_on_fire`
   Routine reads `lessons.md`, `outcomes.json` and the packet from disk instead — same research,
   a fraction of the context. Plausibly **60–75% off** with no quality loss. This is reversible
   and needs no code change.
2. **Cadence.** Weekly instead of daily is ~÷7. Event-driven (run only when a holding changes, a
   score moves >0.2, or a stop comes within 3%) is ~÷3 and keeps the useful days.
3. **Model.** Sonnet 5 is $2/$10 — 2.5× cheaper. Haiku 4.5 is $1/$5 — 5× cheaper. **Your call, not
   mine**; I will not downgrade the model to flatter the cost line.
4. **Scope.** Three memos a day instead of eight.

Stacking (1) and (2) alone gets the desk to roughly **$100–300/year**, which a $10k account can
carry.

## 6. Recommendation

**Do not put real money behind this yet.** Twelve closed trades, zero wins, zero demonstrated edge
from the research layer, and a cost structure that eats the whole expected return at this size.
The trial has not earned a live account.

What it *has* produced that is worth more than it cost, if anyone acts on it:

- **Exits are the broken half.** Buy decisions judge 4-good-of-5; sell decisions **0-of-4**. Seven
  trend-break exits cost −$54.44. Average hold is **2.4–3.2 days on a 55-day-breakout signal** —
  the entry rule and the exit rule are arguing with each other, and two positions (XLV, XLF) were
  bought and sold the same day.
- **`n8` beats the live `n12`** on robustness in two independent weekly walk-forwards
  (`research/proposals/2026-09-07-slots-and-stops.md`, still untested).
- **Relative strength ranks first of ten variants** by robustness and the packet does not compute
  it (`research/proposals/2026-09-13-populate-rs.md`, `rs` empty for nine days).
- **Flat memos are a 40% penalty, not neutrality** — section 2 above.

Those four are the return on the last two weeks. None of them has been implemented.

## 7. The decision

1. **Shut the desk down.** Defensible. The account is too small; the strategy runs without it.
2. **Cut it to weekly + fresh-session-per-run**, implement the four findings above, and judge it
   again in a month against a stated bar (e.g. research-attributed P&L > desk cost).
3. **Keep it daily** only if the account goes to ~$100k+, where the cost is a rounding error.

My recommendation is **2**, and if the findings in section 6 are not implemented within that month,
**1** — because a desk whose output nobody acts on is a pure cost no matter how good the memos are.
