"""Turn the journal into a review packet the weekly review agent can learn from."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import RESEARCH_DIR
from kismat.journal.store import Journal


def trade_stats(fills: list[dict]) -> dict:
    """Pair buys and sells per symbol (FIFO) into closed trades."""
    open_lots: dict[str, list[dict]] = defaultdict(list)
    closed: list[dict] = []
    for f in fills:
        if f["side"] == "buy":
            open_lots[f["symbol"]].append(dict(f))
        else:
            qty = f["qty"]
            while qty > 1e-12 and open_lots[f["symbol"]]:
                lot = open_lots[f["symbol"]][0]
                take = min(qty, lot["qty"])
                pnl = (f["price"] - lot["price"]) * take - f["fee"] * (take / f["qty"]) - lot["fee"] * (take / lot["qty"])
                closed.append({"symbol": f["symbol"], "qty": take, "entry": lot["price"], "exit": f["price"],
                               "pnl": pnl, "pnl_pct": f["price"] / lot["price"] - 1,
                               "entry_ts": lot["timestamp"], "exit_ts": f["timestamp"],
                               "entry_reason": lot.get("reason", ""), "exit_reason": f.get("reason", "")})
                lot["qty"] -= take
                qty -= take
                if lot["qty"] <= 1e-12:
                    open_lots[f["symbol"]].pop(0)
    wins = [t for t in closed if t["pnl"] > 0]
    losses = [t for t in closed if t["pnl"] <= 0]
    return {
        "closed_trades": len(closed),
        "win_rate": len(wins) / len(closed) if closed else 0.0,
        "avg_win_pct": sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0.0,
        "avg_loss_pct": sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0.0,
        "total_pnl": sum(t["pnl"] for t in closed),
        "by_exit_reason": _group(closed, "exit_reason"),
        "by_symbol": _group(closed, "symbol"),
        "trades": closed,
    }


def _group(trades: list[dict], key: str) -> dict:
    out: dict[str, dict] = defaultdict(lambda: {"n": 0, "pnl": 0.0})
    for t in trades:
        g = out[t.get(key, "")]
        g["n"] += 1
        g["pnl"] += t["pnl"]
    return {k: {"n": v["n"], "pnl": round(v["pnl"], 2)} for k, v in out.items()}


def build_review_packet(journal: Journal, root: Path | None = None) -> Path:
    root = root or RESEARCH_DIR
    today = datetime.now(timezone.utc).date().isoformat()
    fills = journal.read("fills")
    equity = journal.read("equity")
    events = journal.read("events", limit=50)
    stats = trade_stats(fills)
    out = root / "reviews"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{today}.md"
    lines = [f"# Weekly review packet {today}", "",
             "Run prompts/weekly_review.md against this file. Output goes to research/reviews/" + today + "-review.md",
             "and any rule change proposals go to research/proposals/ as a PR, never straight into config.", "",
             "## Equity",
             f"- snapshots: {len(equity)}",
             f"- first: {equity[0]['equity'] if equity else 'n/a'}",
             f"- last: {equity[-1]['equity'] if equity else 'n/a'}",
             f"- max drawdown seen: {min((e.get('drawdown', 0) for e in equity), default=0):.2%}", "",
             "## Trades",
             f"- closed: {stats['closed_trades']}, win rate {stats['win_rate']:.0%}, "
             f"avg win {stats['avg_win_pct']:+.2%}, avg loss {stats['avg_loss_pct']:+.2%}, "
             f"total pnl {stats['total_pnl']:+.2f}",
             "- by exit reason: " + ", ".join(f"{k}: n={v['n']} pnl={v['pnl']}" for k, v in stats["by_exit_reason"].items()),
             "- by symbol: " + ", ".join(f"{k}: n={v['n']} pnl={v['pnl']}" for k, v in stats["by_symbol"].items()), ""]
    lines.append("## Last 30 closed trades")
    for t in stats["trades"][-30:]:
        lines.append(f"- {t['symbol']} {t['entry_ts'][:10]} -> {t['exit_ts'][:10]} {t['pnl_pct']:+.2%} "
                     f"| in: {t['entry_reason']} | out: {t['exit_reason']}")
    lines.append("")
    lines.append("## Recent events")
    for e in events[-20:]:
        lines.append(f"- {e['ts']} {e['kind']}: {e['message']}")
    path.write_text("\n".join(lines) + "\n")
    return path
