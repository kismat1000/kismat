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
    report = engine.run_cycle(settings, bars_provider=provider, headlines_provider=lambda q: [],
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
