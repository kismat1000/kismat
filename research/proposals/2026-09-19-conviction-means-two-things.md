# Proposal: `conviction` means two incompatible things, and the desk can only subtract

- date: 2026-09-19
- author: council/desk
- status: proposed (no code changed; `config/` and `kismat/` are out of scope for this routine)
- supersedes nothing; explains the finding in `research/viability.md` §2

## The defect

`prompts/00_desk_rules.md` defines conviction as **confidence**: "0.9 means you would be shocked
to be wrong. 0.5 means a coin flip. Most honest memos land between 0.3 and 0.7."

`kismat/engine.py` uses it as a **score on the same 0–1 scale as the systematic score**:

```
combined = 0.6 * systematic + 0.4 * research        # RESEARCH_WEIGHT = 0.4
research = sign * conviction * decay                # sign: long +1, flat 0, avoid −1
```

For a memo to leave a score unchanged, `conviction` must **equal** the systematic score. To
improve it, conviction must **exceed** it.

Trend-following scores on trending assets run 0.55–0.85. Honest confidence, per the desk rules,
runs 0.3–0.7 and "most honest memos land between 0.3 and 0.7". **The two ranges barely overlap, and
the desk's sits lower.** An honest desk following its own rules can therefore only ever subtract.

## Evidence: every live memo is a drag

All thirteen memos in force on 2026-09-19, against the systematic scores in today's packet:

| symbol | systematic | research | combined | drag | below 0.35 entry threshold |
|---|---|---|---|---|---|
| ETHUSDT | 0.85 | 0.000 | 0.510 | **−0.340** | |
| LINKUSDT | 0.65 | 0.000 | 0.390 | −0.260 | |
| BNBUSDT | 0.65 | 0.000 | 0.390 | −0.260 | |
| BTCUSDT | 0.60 | 0.000 | 0.360 | −0.240 | |
| XLE | 0.55 | 0.000 | 0.330 | −0.220 | **yes** |
| DBC | 0.54 | 0.000 | 0.324 | −0.216 | **yes** |
| XLV | 0.48 | 0.000 | 0.288 | −0.192 | **yes** |
| AAPL | 0.48 | 0.000 | 0.288 | −0.192 | **yes** |
| MSFT | 0.65 | 0.225 | 0.480 | −0.170 | |
| XLK | 0.34 | 0.000 | 0.204 | −0.136 | |
| CSL.AX | 0.65 | 0.367 | 0.537 | −0.113 | |
| SOLUSDT | 0.65 | 0.417 | 0.557 | −0.093 | |

**Not one memo raises a score.** Including the three longs: a long at conviction 0.45 on a 0.65
systematic score is a 0.17 haircut. Meanwhile the two candidates with **no** memo — AVAXUSDT (0.60)
and AMD (0.59) — carry their full systematic score and now outrank six researched holdings.

## What this has actually cost so far: nothing, by luck

- **Rotation is off.** `rotation_margin: 0.0` and the engine gates on `rotation_margin > 0`; there
  are zero rotation fills in the journal. Had the margin been any positive number, the suppressed
  holdings would have been the weakest in the book and AVAX/AMD would have replaced them.
- **The exit threshold is −0.10**, far below any combined score, so no exit has been triggered.
- **The live exposure is re-entry blocking**: XLE, DBC, XLV and AAPL now sit below the 0.35 entry
  threshold *purely because of a flat memo*. If any were stopped out and re-qualified, the memo
  would block re-entry.

So the drag is real and large but has not yet cost a trade. That is an accident of configuration,
not a design that works.

## The deeper point

"Flat" is not neutrality — it is a 40% haircut. The neutral act in this engine is **writing no memo
at all** (`research = None` → `combined = systematic`). Roughly 80% of the 69 memos written in two
weeks are flat, so for two weeks the desk's dominant output has been an unacknowledged penalty.

## Proposed changes

1. **Exclude `flat` from scoring.** `Memo.score()` should return `None` for `flat`, and
   `combined_score` should treat it as no memo. A desk saying "no edge" should leave the systematic
   score alone, which is what the desk rules plainly intend. This is the single-line fix.
2. **Cut `RESEARCH_WEIGHT` from 0.40 until the desk demonstrates edge.** On the current record —
   long memos 4 good of 11 judged (0.36), skip decisions 2 of 15 (0.13), 12 closed trades and 0
   wins — 40% of the score is unearned. 0.10–0.15 is defensible; restore it if and when the record
   supports it.
3. **Reconcile the two definitions of conviction.** Either the desk rules adopt the engine's
   meaning ("what score does this asset deserve", which invites inflation and should be resisted),
   or the engine stops reading confidence as a score — for example
   `combined = systematic * (1 + k * signed_confidence)`, where an honest 0.5 confidence is
   genuinely neutral. The second is the better fix; the first only looks like one.

## Why this might be wrong

If the desk's flat calls are genuinely good, the haircut is a feature and removing it would let
weak names back in. The record does not support that reading — skip decisions judge 2-good-of-15 —
but the sample is small and the judging window re-scores past calls violently (the long hit rate
has printed 0.43, 0.86, 0.375, 0.625, 0.40 and 0.36 on consecutive days). Change (1) is safe under
either reading. Change (2) is the one that needs a real decision.
