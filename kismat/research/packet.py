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
                 native_prices: dict[str, float] | None = None) -> Path:
    native_prices = native_prices or {}
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
    lines.append("| symbol | score | close (USD) | native | rsi | 3m | atr% |")
    lines.append("|---|---|---|---|---|---|---|")
    for sym in sorted(signals, key=lambda s: -signals[s]["score"]):
        sig = signals[sym]
        f = sig.get("features", {})
        native = f"A${native_prices[sym]:.2f}" if sym in native_prices else "-"
        lines.append(f"| {sym} | {sig['score']:+.2f} | {sig.get('close', float('nan')):.6g} | {native} | "
                     f"{f.get('rsi14', float('nan')):.0f} | {f.get('roc63', 0):+.1%} | {f.get('atr_pct', 0):.1%} |")
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
