"""Build the research packet: everything a research agent needs in one file.

The packet is markdown so a Claude Code Routine (or you, or an API call) can
read it, run the council prompts, and write memos back into research/memos/.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import RESEARCH_DIR, ROOT


def build_packet(signals: dict[str, dict], positions: dict[str, dict], headlines: list[dict],
                 memos: dict[str, dict], equity: float, cash: float,
                 candidates: list[str], root: Path | None = None, fx: float | None = None,
                 native_prices: dict[str, float] | None = None, tones: dict[str, dict] | None = None,
                 blackout: dict[str, str] | None = None) -> Path:
    native_prices = native_prices or {}
    tones = tones or {}
    blackout = blackout or {}
    root = root or RESEARCH_DIR
    today = datetime.now(timezone.utc).date().isoformat()
    out_dir = root / "packets"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.md"

    lines = [f"# Research packet {today}", "",
             "Read prompts/00_desk_rules.md first, then run the council prompts in prompts/ for each",
             "candidate below. Write one memo per symbol to research/memos/" + today + "/<SYMBOL>.json",
             "following prompts/memo_schema.json. Do not write memos for symbols you did not research.",
             "",
             f"## Account", f"- equity: {equity:.2f}", f"- cash: {cash:.2f}",
             f"- open positions: {len(positions)}",
             (f"- all prices are USD; ASX symbols were converted at AUDUSD {fx:.4f}, native AUD shown in the "
              f"`native` column" if fx else "- all prices are USD"), ""]
    if positions:
        lines.append("## Open positions (review these first: should we still hold?)")
        for sym, p in positions.items():
            pnl = (p.get("last_price", p["avg_price"]) / p["avg_price"] - 1)
            lines.append(f"- {sym} ({p['asset_class']}): qty {p['qty']:.6g} avg {p['avg_price']:.6g} "
                         f"last {p.get('last_price', p['avg_price']):.6g} pnl {pnl:+.1%}")
        lines.append("")
    lines.append("## Candidates (systematic score, highest first)")
    ranked = sorted(((signals[s]["score"], s) for s in candidates if s in signals), reverse=True)
    for score, sym in ranked:
        sig = signals[sym]
        memo_note = ""
        if sym in memos:
            m = memos[sym]
            memo_note = f" | existing memo: {m['direction']} {m['conviction']:.2f} ({m['date']})"
        lines.append(f"- {sym}: score {score:+.2f}; " + "; ".join(sig.get("reasons", [])) + memo_note)
    lines.append("")
    lines.append("## Full signal table")
    lines.append("52w = distance below the 252-day high; rs = momentum minus the class benchmark's; "
                 "squeeze = ATR% against its 100-day median (below 0.75 is a squeeze); "
                 "news = headline tone -1..+1 from today's symbol headlines, ! = hard-negative headline.")
    lines.append("| symbol | score | close (USD) | native | rsi | 3m | atr% | 52w | rs | squeeze | news |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for sym in sorted(signals, key=lambda s: -signals[s]["score"]):
        sig = signals[sym]
        f = sig.get("features", {})
        native = f"A${native_prices[sym]:.2f}" if sym in native_prices else "-"
        nh, rs, ar = f.get("near_high"), f.get("rs"), f.get("atr_ratio")
        col_52w = f"{1 - nh:.1%}" if isinstance(nh, (int, float)) and nh == nh else "-"
        col_rs = f"{rs:+.1%}" if isinstance(rs, (int, float)) and rs == rs else "-"
        col_sq = f"{ar:.2f}" if isinstance(ar, (int, float)) and ar == ar else "-"
        t = tones.get(sym)
        col_news = (f"{t['score']:+.2f}" + ("!" if t.get("flags") else "")) if t and t.get("headlines") else "-"
        lines.append(f"| {sym} | {sig['score']:+.2f} | {sig.get('close', float('nan')):.6g} | {native} | "
                     f"{f.get('rsi', float('nan')):.0f} | {f.get('roc_mom', 0):+.1%} | {f.get('atr_pct', 0):.1%} | "
                     f"{col_52w} | {col_rs} | {col_sq} | {col_news} |")
    lines.append("")
    flagged = {s: t for s, t in tones.items() if t.get("flags")}
    if flagged or blackout:
        lines.append("## Event and news gates in force today")
        for s, t in flagged.items():
            lines.append(f"- {s}: no new entry, hard-negative headline: {t['flags'][0]}")
        for s, d in blackout.items():
            lines.append(f"- {s}: no new entry, earnings on {d}")
        lines.append("")
    lines.append(f"## Headlines ({len(headlines)})")
    for h in headlines[:80]:
        lines.append(f"- [{h.get('source','')}] {h.get('title','')} ({h.get('published','')}) {h.get('link','')}")
    lines.append("")
    lines.append("## Memo schema")
    lines.append("```json")
    lines.append((ROOT / "prompts" / "memo_schema.json").read_text().strip()
                 if (ROOT / "prompts" / "memo_schema.json").exists() else "{}")
    lines.append("```")
    path.write_text("\n".join(lines) + "\n")
    (out_dir / "latest.json").write_text(json.dumps({"date": today, "candidates": [s for _, s in ranked],
                                                    "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}, indent=2))
    return path
