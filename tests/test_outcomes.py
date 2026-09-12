import json
from datetime import timedelta

import pandas as pd

from kismat.data.prices import synthetic_bars
from kismat.journal import outcomes as O


def _closes(days=60, up=True):
    df = synthetic_bars(days, drift=0.01 if up else -0.01, vol=0.001, seed=5)
    return df["close"]


def test_forward_and_verdict():
    closes = _closes()
    start = closes.index[10]
    f = O.forward(closes, start, float(closes.iloc[10]))
    assert f["now"] > 0 and f["horizon"] > 0 and f["horizon"] < f["now"]
    assert O.forward(closes, closes.index[-1], None)["horizon"] is None       # no bars 5 days later yet
    assert O.forward(None, start, 1.0) == {"now": None, "horizon": None}
    assert O.verdict(0.05, True) == "good" and O.verdict(0.05, False) == "bad"
    assert O.verdict(-0.05, False) == "good" and O.verdict(0.001, True) == "flat"
    assert O.verdict(None, True) == "" and O.verdict(0.1, None) == ""


def test_closed_trades_get_verdicts_and_lessons():
    t0 = "2026-09-01T10:00:00+00:00"
    fills = [{"symbol": "A", "side": "buy", "qty": 10, "price": 100.0, "fee": 0.1, "timestamp": t0, "ts": t0, "reason": "uptrend"},
             {"symbol": "A", "side": "sell", "qty": 10, "price": 120.0, "fee": 0.1, "timestamp": "2026-09-20T10:00:00+00:00",
              "ts": "2026-09-20T10:00:00+00:00", "reason": "trailing stop hit (118 <= 119)"},
             {"symbol": "B", "side": "buy", "qty": 5, "price": 50.0, "fee": 0.1, "timestamp": t0, "ts": t0, "reason": "breakout"},
             {"symbol": "B", "side": "sell", "qty": 5, "price": 47.0, "fee": 0.1, "timestamp": "2026-09-03T10:00:00+00:00",
              "ts": "2026-09-03T10:00:00+00:00", "reason": "trend break: below fast SMA and underwater"}]
    memos = [{"symbol": "B", "date": "2026-08-30", "direction": "long", "conviction": 0.8}]
    trades = O.closed_trades(fills, memos)
    a, b = trades
    assert a["verdict"] == "good" and a["hold_days"] == 19 and "Winner ran" in a["lesson"]
    assert b["verdict"] == "bad" and b["hold_days"] == 2 and "within 2 day" in b["lesson"]
    assert b["memo_direction"] == "long" and "Research was long at entry and wrong" in b["lesson"]
    s = O.summarize(trades, [], [])
    assert s["closed_trades"] == 2 and s["wins"] == 1 and s["win_rate"] == 0.5 and s["realized_pnl"] > 0
    assert "trailing stop hit" in s["by_exit_reason"] and s["by_memo_at_entry"]["long"]["n"] == 1


def test_decision_and_memo_outcomes():
    up = _closes(up=True)
    start = up.index[20]
    closes = {"UP": up}
    decisions = [{"ts": start.isoformat(), "symbol": "UP", "action": "buy", "price": float(up.iloc[20])},
                 {"ts": start.isoformat(), "symbol": "UP", "action": "skip", "price": float(up.iloc[20]), "reason": "news veto: x"},
                 {"ts": start.isoformat(), "symbol": "UP", "action": "hold"},
                 {"ts": start.isoformat(), "symbol": "NONE", "action": "buy", "price": 1.0}]
    out = O.decision_outcomes(decisions, closes)
    assert [d["verdict"] for d in out] == ["good", "bad", ""]
    memos = [{"symbol": "UP", "date": str(up.index[20].date()), "direction": "long", "conviction": 0.7},
             {"symbol": "UP", "date": str(up.index[20].date()), "direction": "avoid", "conviction": 0.7},
             {"symbol": "UP", "date": str(up.index[20].date()), "direction": "flat", "conviction": 0.5}]
    mo = O.memo_outcomes(memos, closes)
    assert [m["verdict"] for m in mo] == ["good", "bad", "flat"]
    s = O.summarize([], out, mo)
    assert s["memos"]["by_direction"]["long"]["hit_rate"] == 1.0 and s["gates"]["judged"] == 1
    assert s["decisions"]["buy"]["good"] == 1


def test_update_lessons_is_idempotent(tmp_path):
    trade = {"symbol": "A", "exit_ts": "2026-09-20T10:00:00+00:00", "pnl": 3.0, "pnl_pct": 0.03, "hold_days": 4,
             "entry_reason": "uptrend", "exit_reason": "trailing stop", "lesson": "Winner ran.", "key": "A@2026-09-20T10:00:00"}
    path = tmp_path / "lessons.md"
    assert O.update_lessons(path, [trade]) == 1
    assert O.update_lessons(path, [trade]) == 0
    text = path.read_text()
    assert text.count("A@2026-09-20") == 1 and "WIN +3.00%" in text and text.startswith("# Lessons")
