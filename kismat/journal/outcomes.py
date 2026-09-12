"""Was it profitable? Green or red on everything, and a lesson from every trade.

The journal records what the system decided and why. This module joins those
records with what prices did afterwards, so every closed trade, every decision
(a buy, a skip, a sell, a gate), and every research memo carries a verdict:

- a closed trade is green when its P&L after costs is positive;
- a buy is green when the price rose after it; a skip, a sell, or a gate is
  green when the price fell after it (the decision avoided a loss);
- a memo is green when the price moved the way it said (long: up, avoid: down).

Every closed trade also gets a one-line lesson from plain rules, appended once
to research/lessons.md, which the research desk reads before writing memos.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from kismat.journal.review import trade_stats
from kismat.research.memos import memo_dir, validate

log = logging.getLogger(__name__)
FLAT = 0.003          # moves smaller than this are "flat", neither green nor red
HORIZON_DAYS = 5      # the fixed look-ahead for decisions and memos


def _ts(value) -> pd.Timestamp:
    t = pd.Timestamp(value)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def forward(closes: pd.Series | None, start: pd.Timestamp, from_price: float | None,
            horizon_days: int = HORIZON_DAYS) -> dict:
    """Return since `start` from `from_price` to the latest close and to the first
    close at least `horizon_days` later. None where prices do not reach."""
    out = {"now": None, "horizon": None}
    if closes is None or len(closes) == 0:
        return out
    if from_price is None or from_price <= 0:
        before = closes[closes.index <= start]
        if len(before) == 0:
            return out
        from_price = float(before.iloc[-1])
    out["now"] = float(closes.iloc[-1]) / from_price - 1
    later = closes[closes.index >= start + timedelta(days=horizon_days)]
    if len(later):
        out["horizon"] = float(later.iloc[0]) / from_price - 1
    return out


def verdict(move: float | None, wants_up: bool | None) -> str:
    """'good', 'bad', 'flat', or '' (no view or no data)."""
    if move is None or wants_up is None:
        return ""
    if abs(move) < FLAT:
        return "flat"
    return "good" if (move > 0) == wants_up else "bad"


# ---- closed trades and lessons -------------------------------------------------------
def _hold_days(t: dict) -> int:
    try:
        return max((_ts(t["exit_ts"]) - _ts(t["entry_ts"])).days, 0)
    except Exception:
        return 0


def lesson_for(t: dict) -> str:
    pnl, days, why = t["pnl_pct"], t.get("hold_days", 0), (t.get("exit_reason") or "").lower()
    memo = t.get("memo_direction")
    if "kill switch" in why or "halt" in why:
        base = "Closed by the kill switch, not by the trade itself: the account-level drawdown rule fired."
    elif "rotation" in why:
        base = (f"Rotated out for a stronger candidate after {days} days at {pnl:+.1%}: "
                "judge rotation by what the replacement did, not by this exit.")
    elif "trailing stop" in why and pnl > 0:
        base = f"Winner ran {days} days for {pnl:+.1%} and the trailing stop took the profit when the trend paused."
    elif "trailing stop" in why:
        base = (f"Trailing stop hit below entry after {days} days ({pnl:+.1%}): the move never got going; "
                "the ATR stop did its job and capped the loss.")
    elif "trend break" in why and days <= 3:
        base = (f"Trend broke within {days} day(s) of entry ({pnl:+.1%}): the move reversed right after the "
                "entry. Check the RSI and the distance from the 55-day high at entry; a cluster of these in "
                "one week usually means the whole market turned, not that each pick was wrong.")
    elif "trend break" in why:
        base = f"Trend broke while underwater after {days} days ({pnl:+.1%}): momentum did not follow through."
    elif "score turned negative" in why:
        base = f"Systematic score turned negative after {days} days ({pnl:+.1%}): the setup decayed before the stop was hit."
    elif "time stop" in why:
        base = f"Time stop after {days} days underwater ({pnl:+.1%}): dead money was recycled."
    elif pnl > 0:
        base = f"Closed for {pnl:+.1%} after {days} days."
    else:
        base = f"Closed for {pnl:+.1%} after {days} days."
    if memo == "long" and pnl < 0:
        base += " Research was long at entry and wrong."
    elif memo == "long" and pnl > 0:
        base += " Research was long at entry and right."
    elif memo == "flat" and pnl < 0:
        base += " Research was flat at entry: the systematic score alone carried this one."
    return base


def _memo_at(memos_all: list[dict], symbol: str, when: pd.Timestamp, max_age_days: int = 5) -> dict | None:
    best = None
    for m in memos_all:
        if m["symbol"] != symbol:
            continue
        age = (when.date() - datetime.fromisoformat(m["date"]).date()).days
        if 0 <= age <= max_age_days and (best is None or m["date"] >= best["date"]):
            best = m
    return best


def closed_trades(fills: list[dict], memos_all: list[dict] | None = None) -> list[dict]:
    trades = trade_stats(fills)["trades"]
    for t in trades:
        t["hold_days"] = _hold_days(t)
        m = _memo_at(memos_all or [], t["symbol"], _ts(t["entry_ts"]))
        t["memo_direction"] = m["direction"] if m else None
        t["memo_conviction"] = m["conviction"] if m else None
        t["verdict"] = "good" if t["pnl"] > 0 else "bad"
        t["lesson"] = lesson_for(t)
        t["key"] = f"{t['symbol']}@{t['exit_ts'][:19]}"
    return trades


# ---- decisions -----------------------------------------------------------------------
def decision_outcomes(decisions: list[dict], closes: dict[str, pd.Series]) -> list[dict]:
    out = []
    for d in decisions:
        action = d.get("action")
        if action in (None, "hold"):
            continue
        rec = dict(d)
        try:
            start = _ts(d["ts"])
            fwd = forward(closes.get(d["symbol"]), start, d.get("price"))
        except Exception:
            fwd = {"now": None, "horizon": None}
        wants_up = True if action in ("buy", "proposed", "approved") else False if action in ("skip", "sell", "rejected") else None
        rec["since"] = fwd["now"]
        rec["horizon"] = fwd["horizon"]
        rec["verdict"] = verdict(fwd["horizon"] if fwd["horizon"] is not None else fwd["now"], wants_up)
        out.append(rec)
    return out


# ---- memos ---------------------------------------------------------------------------
def load_all_memos(root: Path | None = None) -> list[dict]:
    base = memo_dir(root)
    out = []
    if not base.exists():
        return out
    for path in sorted(base.glob("*/*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not validate(data):
            out.append(data)
    return out


def memo_outcomes(memos_all: list[dict], closes: dict[str, pd.Series]) -> list[dict]:
    out = []
    for m in memos_all:
        start = _ts(m["date"]) + timedelta(hours=23, minutes=59)   # the memo saw that day's close
        fwd = forward(closes.get(m["symbol"]), start, None)
        wants_up = {"long": True, "avoid": False, "flat": None}.get(m["direction"])
        move = fwd["horizon"] if fwd["horizon"] is not None else fwd["now"]
        out.append({"symbol": m["symbol"], "date": m["date"], "direction": m["direction"],
                    "conviction": float(m["conviction"]), "since": fwd["now"], "horizon": fwd["horizon"],
                    "verdict": verdict(move, wants_up) if m["direction"] != "flat" else ("flat" if move is not None else "")})
    return out


# ---- summary -------------------------------------------------------------------------
def _rate(items: list[dict]) -> dict:
    judged = [i for i in items if i.get("verdict") in ("good", "bad")]
    good = sum(1 for i in judged if i["verdict"] == "good")
    return {"n": len(items), "judged": len(judged), "good": good,
            "hit_rate": good / len(judged) if judged else None}


def summarize(trades: list[dict], decisions: list[dict], memos: list[dict]) -> dict:
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    by_reason: dict[str, dict] = {}
    for t in trades:
        key = (t.get("exit_reason") or "").split(":")[0].split("(")[0].strip()[:40] or "other"
        g = by_reason.setdefault(key, {"n": 0, "pnl": 0.0, "wins": 0})
        g["n"] += 1
        g["pnl"] += t["pnl"]
        g["wins"] += 1 if t["pnl"] > 0 else 0
    by_memo: dict[str, dict] = {}
    for t in trades:
        key = t.get("memo_direction") or "no memo"
        g = by_memo.setdefault(key, {"n": 0, "pnl": 0.0, "wins": 0})
        g["n"] += 1
        g["pnl"] += t["pnl"]
        g["wins"] += 1 if t["pnl"] > 0 else 0
    memo_by_dir = {d: _rate([m for m in memos if m["direction"] == d]) for d in ("long", "avoid")}
    memo_by_conv = {"high (>=0.7)": _rate([m for m in memos if m["conviction"] >= 0.7 and m["direction"] != "flat"]),
                    "mid (0.5-0.7)": _rate([m for m in memos if 0.5 <= m["conviction"] < 0.7 and m["direction"] != "flat"]),
                    "low (<0.5)": _rate([m for m in memos if m["conviction"] < 0.5 and m["direction"] != "flat"])}
    gates = [d for d in decisions if d.get("action") == "skip"
             and any(k in (d.get("reason") or "") for k in ("news veto", "earnings on", "regime", "veto"))]
    return {
        "closed_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": len(wins) / len(trades) if trades else None,
        "realized_pnl": sum(t["pnl"] for t in trades),
        "avg_win_pct": sum(t["pnl_pct"] for t in wins) / len(wins) if wins else None,
        "avg_loss_pct": sum(t["pnl_pct"] for t in losses) / len(losses) if losses else None,
        "expectancy_pct": sum(t["pnl_pct"] for t in trades) / len(trades) if trades else None,
        "avg_hold_days": sum(t["hold_days"] for t in trades) / len(trades) if trades else None,
        "by_exit_reason": by_reason, "by_memo_at_entry": by_memo,
        "decisions": {a: _rate([d for d in decisions if d.get("action") == a]) for a in ("buy", "skip", "sell", "proposed")},
        "gates": _rate(gates),
        "memos": {"by_direction": memo_by_dir, "by_conviction": memo_by_conv, "all": _rate([m for m in memos if m["direction"] != "flat"])},
    }


# ---- lessons file and build ---------------------------------------------------------
def update_lessons(path: Path, trades: list[dict]) -> int:
    """Append one line per newly closed trade. Returns how many were added."""
    existing = path.read_text() if path.exists() else ""
    new = [t for t in trades if f"<!-- {t['key']} -->" not in existing]
    if not new:
        return 0
    lines = [] if existing else ["# Lessons from every closed trade", "",
                                 "One line per trade, written by rule from the journal when the trade closed.",
                                 "The research desk reads the newest entries before writing memos.", ""]
    for t in new:
        mark = "WIN" if t["pnl"] > 0 else "LOSS"
        lines.append(f"- {t['exit_ts'][:10]} **{t['symbol']}** {mark} {t['pnl_pct']:+.2%} ({t['pnl']:+.2f}) "
                     f"held {t['hold_days']}d, in: {t['entry_reason'][:70]}; out: {t['exit_reason'][:60]}. "
                     f"{t['lesson']} <!-- {t['key']} -->")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing.rstrip("\n") + ("\n" if existing else "") + "\n".join(lines) + "\n")
    return len(new)


def build(journal, bars: dict[str, pd.DataFrame], research_dir: Path, decision_limit: int = 80) -> dict:
    closes = {s: df["close"] for s, df in bars.items() if df is not None and "close" in df}
    memos_all = load_all_memos(research_dir)
    trades = closed_trades(journal.read("fills"), memos_all)
    decisions = decision_outcomes(journal.read("decisions", limit=decision_limit), closes)
    memos = memo_outcomes(memos_all, closes)
    result = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
              "summary": summarize(trades, decisions, memos), "trades": trades[-60:],
              "decisions": decisions, "memos": memos[-80:]}
    try:
        research_dir.mkdir(parents=True, exist_ok=True)
        (research_dir / "outcomes.json").write_text(json.dumps(result, indent=1, default=str))
        update_lessons(research_dir / "lessons.md", trades)
    except Exception as exc:
        log.warning("outcomes not written: %s", exc)
    return result
