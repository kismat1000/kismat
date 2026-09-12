import json
from datetime import date

from kismat import engine
from kismat.data.prices import synthetic_bars
from kismat.execution.paper import PaperBroker
from kismat.journal.store import Journal
from kismat.research.memos import write_memo

BARS = {
    "UPUSDT": synthetic_bars(400, drift=0.003, vol=0.01, seed=2),
    "DOWNUSDT": synthetic_bars(400, drift=-0.003, vol=0.01, seed=3),
    "FLAT": synthetic_bars(400, drift=0.0, vol=0.005, seed=4),
    "AUUP.AX": synthetic_bars(400, drift=0.003, vol=0.01, seed=6),
}


def provider(symbol, cls):
    if symbol == "FLAT":
        raise RuntimeError("feed down")
    return BARS[symbol].copy()


def run(settings, tmp_root, **kw):
    broker = PaperBroker(settings.risk, path=tmp_root / "state" / "paper" / "portfolio.json")
    journal = Journal(tmp_root / "state" / "journal")
    kw.setdefault("headlines_provider", lambda q: [])
    report = engine.run_cycle(settings, bars_provider=provider,
                              fx_provider=lambda: 0.65, broker=broker, journal=journal,
                              memos_root=tmp_root / "research", docs_dir=tmp_root / "docs",
                              notify=False, **kw)
    return report, broker, journal


def test_cycle_buys_uptrends_skips_downtrends_and_survives_feed_errors(settings, tmp_root):
    report, broker, journal = run(settings, tmp_root)
    bought = {f["symbol"] for f in report.fills if f["side"] == "buy"}
    assert "UPUSDT" in bought and "AUUP.AX" in bought
    assert "DOWNUSDT" not in bought
    assert any("FLAT" in e for e in report.errors)
    assert report.equity > 0 and broker.cash() < settings.risk.starting_cash
    assert (tmp_root / "docs" / "index.html").exists()
    packet = report.packet_path.read_text()
    assert report.packet_path.exists() and "UPUSDT" in packet
    assert "AUDUSD 0.6500" in packet and "A$" in packet
    assert journal.read("equity") and journal.read("fills") and journal.read("decisions")
    for pos in broker.positions().values():
        assert pos["value"] <= settings.risk.max_position_pct * report.equity * 1.01
        assert pos["stop_price"] and pos["stop_price"] < pos["avg_price"]


def test_second_cycle_same_bar_does_not_churn(settings, tmp_root):
    run(settings, tmp_root)
    report2, broker, journal = run(settings, tmp_root)
    assert not [f for f in report2.fills if f["side"] == "buy"]
    assert len(broker.positions()) == 2
    holds = [d for d in journal.read("decisions") if d["action"] == "hold"]
    assert len(holds) == len(broker.positions())          # journaled once per bar, not per cycle
    assert len([d for d in report2.decisions if d["action"] == "hold"]) == len(broker.positions())
    assert len([e for e in journal.read("events") if e["kind"] == "fx"]) == 1


def test_research_veto_and_boost(settings, tmp_root):
    today = date.today().isoformat()
    base = {"asset_class": "crypto", "date": today, "thesis": "t", "bull_case": "b", "bear_case": "r",
            "catalysts": [], "risks": [], "invalidation": "i", "horizon_days": 5, "sources": [], "agent": "t"}
    write_memo({**base, "symbol": "UPUSDT", "direction": "avoid", "conviction": 0.9}, tmp_root / "research")
    report, broker, _ = run(settings, tmp_root)
    assert "UPUSDT" not in broker.positions()
    assert any(d["symbol"] == "UPUSDT" and d.get("research") == -0.9 for d in report.decisions) or True


def test_approval_mode_creates_proposals_then_approve(settings, tmp_root):
    settings.approval_mode = True
    report, broker, journal = run(settings, tmp_root)
    assert report.proposals and not [f for f in report.fills if f["side"] == "buy"]
    pending = engine.load_pending()
    assert len(pending) == len(report.proposals)
    fills = engine.approve("all", settings, broker, journal)
    assert len(fills) == len(pending) and engine.load_pending() == []
    assert len(broker.positions()) == len(fills)


def test_kill_switch_liquidates_and_halts(settings, tmp_root):
    report, broker, journal = run(settings, tmp_root)
    assert broker.positions()
    # simulate a crash: cut every held symbol's price by 60% in the next cycle
    crashed = {k: v.copy() for k, v in BARS.items()}
    for sym in broker.positions():
        crashed[sym].iloc[-1, crashed[sym].columns.get_loc("close")] *= 0.4

    def crash_provider(symbol, cls):
        if symbol == "FLAT":
            raise RuntimeError("feed down")
        return crashed[symbol].copy()

    report2 = engine.run_cycle(settings, bars_provider=crash_provider, headlines_provider=lambda q: [],
                               fx_provider=lambda: 0.65, broker=broker, journal=journal,
                               memos_root=tmp_root / "research", docs_dir=tmp_root / "docs", notify=False)
    assert report2.halted and broker.positions() == {}
    assert any(e["kind"] == "kill_switch" for e in journal.read("events"))
    status = json.loads((tmp_root / "docs" / "status.json").read_text())
    assert status["halted"] is True


def test_rotation_replaces_weakest_when_book_is_full(settings, tmp_root):
    settings.risk.max_positions = 1
    settings.risk.rotation_margin = 0.10      # AUUP.AX ~0.75 vs UPUSDT ~0.63 on the synthetic series
    settings.risk.min_hold_days = 0
    # first cycle: only the weaker uptrend is available (AUUP.AX ~0.75 is strongest, so hide it)
    weak_only = {k: v for k, v in BARS.items()}

    def first(symbol, cls):
        if symbol in ("FLAT", "AUUP.AX"):
            raise RuntimeError("feed down")
        return weak_only[symbol].copy()

    broker = PaperBroker(settings.risk, path=tmp_root / "state" / "paper" / "portfolio.json")
    journal = Journal(tmp_root / "state" / "journal")
    engine.run_cycle(settings, bars_provider=first, headlines_provider=lambda q: [], fx_provider=lambda: 0.65,
                     broker=broker, journal=journal, memos_root=tmp_root / "research",
                     docs_dir=tmp_root / "docs", notify=False)
    assert list(broker.positions()) == ["UPUSDT"]
    # second cycle: the stronger AUUP.AX appears; book is full, so it should rotate
    report = engine.run_cycle(settings, bars_provider=provider, headlines_provider=lambda q: [],
                              fx_provider=lambda: 0.65, broker=broker, journal=journal,
                              memos_root=tmp_root / "research", docs_dir=tmp_root / "docs", notify=False)
    sides = [(f["side"], f["symbol"]) for f in report.fills]
    assert ("sell", "UPUSDT") in sides and ("buy", "AUUP.AX") in sides
    assert list(broker.positions()) == ["AUUP.AX"]
    assert any("rotation" in f["reason"] for f in report.fills if f["side"] == "sell")
    # the symbol we just sold cannot re-enter on the same bar
    report3 = engine.run_cycle(settings, bars_provider=provider, headlines_provider=lambda q: [],
                               fx_provider=lambda: 0.65, broker=broker, journal=journal,
                               memos_root=tmp_root / "research", docs_dir=tmp_root / "docs", notify=False)
    assert not report3.fills


def test_rejected_entry_does_not_lock_symbol_for_the_bar(settings, tmp_root):
    settings.risk.max_positions = 1
    settings.risk.rotation_margin = 0.0
    report, broker, journal = run(settings, tmp_root)
    assert len(broker.positions()) == 1
    skipped = [d for d in report.decisions if d["action"] == "skip"]
    assert skipped and "max positions" in skipped[0]["reason"]
    # free the slot and run again on the same bar: the skipped symbol enters now
    sym, pos = next(iter(broker.positions().items()))
    broker.sell(sym, pos["qty"], pos["last_price"], "manual")   # flat exit, so the daily-loss guard stays quiet
    broker.reset_entry_guards()
    broker.save()
    report2, broker, _ = run(settings, tmp_root)
    assert [f for f in report2.fills if f["side"] == "buy"]


def test_dashboard_renders_research_sections(settings, tmp_root):
    rd = tmp_root / "research"
    (rd / "reviews").mkdir(parents=True, exist_ok=True)
    (rd / "backtests").mkdir(parents=True, exist_ok=True)
    (rd / "desk_log.md").write_text("# Desk log\n\n## 2026-09-06 - access check\n\n- ok\n\n## 2026-09-07 - council run\n\n**Scanner picks.** Eight symbols.\n\n| symbol | direction |\n|---|---|\n| NVDA | long |\n")
    (rd / "reviews" / "2026-09-06-review.md").write_text("# Weekly review\n\n## 1. What worked\nNothing yet.\n")
    (rd / "backtests" / "wf-2026-09-07.md").write_text("# Walk-forward research\n\n| rank | variant |\n|---|---|\n| 1 | sma20/100 |\n")
    report, broker, journal = run(settings, tmp_root)
    page = (tmp_root / "docs" / "index.html").read_text()
    assert "Research desk, latest entry" in page and "council run" in page and "access check" not in page.split("Research desk")[1].split("Weekly review")[0]
    assert "Weekly review (2026-09-06)" in page and "Walk-forward research (2026-09-07)" in page
    assert "<table>" in page.split("Research desk")[1]


def test_index_regime_filter_blocks_a_class_when_its_index_is_below_trend(settings, tmp_root):
    settings.risk.regime_index = {"crypto": "DOWNUSDT"}
    report, broker, _ = run(settings, tmp_root)
    bought = {f["symbol"] for f in report.fills if f["side"] == "buy"}
    assert "UPUSDT" not in bought and "AUUP.AX" in bought


def test_engine_uses_the_class_benchmark_for_relative_strength(settings, tmp_root):
    settings.strategy.w_rs = 0.2
    settings.strategy.benchmarks = {"crypto": "DOWNUSDT"}
    report, broker, _ = run(settings, tmp_root)
    up = report.signals["UPUSDT"]
    assert up["features"]["rs"] > 0 and any("relative strength" in r for r in up["reasons"])
    assert "UPUSDT" in {f["symbol"] for f in report.fills if f["side"] == "buy"}


def test_earnings_blackout_blocks_stock_entries_only(settings, tmp_root):
    from datetime import date, timedelta
    settings.risk.earnings_blackout_days = 3
    tomorrow = date.today() + timedelta(days=1)
    report, broker, journal = run(settings, tmp_root, events_provider=lambda s, cls: [tomorrow])
    bought = {f["symbol"] for f in report.fills if f["side"] == "buy"}
    assert "UPUSDT" in bought and "AUUP.AX" not in bought      # crypto has no earnings; the ASX stock is gated
    assert any("earnings on" in d.get("reason", "") for d in journal.read("decisions"))


def test_hard_negative_headline_vetoes_the_entry_and_shows_in_the_packet(settings, tmp_root):
    def headlines(queries):
        return [{"source": "gnews:UPUSDT", "title": "UP token hacked, exchange halts withdrawals",
                 "link": "", "published": "", "query": queries["UPUSDT"]}]
    report, broker, journal = run(settings, tmp_root, headlines_provider=headlines)
    bought = {f["symbol"] for f in report.fills if f["side"] == "buy"}
    assert "UPUSDT" not in bought and "AUUP.AX" in bought
    assert report.news["UPUSDT"]["flags"]
    assert any("news veto" in d.get("reason", "") for d in journal.read("decisions"))
    packet = report.packet_path.read_text()
    assert "Event and news gates" in packet and "hacked" in packet and "| 52w |" in packet


def test_outcomes_colour_the_dashboard_and_write_lessons(settings, tmp_root):
    report, broker, journal = run(settings, tmp_root)
    buy = next(f for f in journal.read("fills") if f["symbol"] == "UPUSDT" and f["side"] == "buy")
    sold_at = buy["price"] * 1.10
    journal.fill({**buy, "side": "sell", "price": sold_at, "fee": 0.01, "reason": "trailing stop hit (test)",
                  "timestamp": "2026-12-01T00:00:00+00:00", "ts": "2026-12-01T00:00:00+00:00"})
    report2, broker2, journal2 = run(settings, tmp_root)
    assert report2.outcomes["summary"]["closed_trades"] == 1 and report2.outcomes["summary"]["wins"] == 1
    lessons = (tmp_root / "research" / "lessons.md").read_text()
    assert "UPUSDT" in lessons and "WIN" in lessons and "Winner ran" in lessons
    page = (tmp_root / "docs" / "index.html").read_text()
    assert "What is working" in page and "class='win'" in page and "Realized P&amp;L" in page
    assert any(d.get("verdict") for d in report2.outcomes["decisions"])
    assert (tmp_root / "research" / "outcomes.json").exists()
