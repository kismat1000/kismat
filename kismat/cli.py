"""Command line entry points. `python -m kismat --help`."""
from __future__ import annotations

import argparse
import json
import logging
import sys

from kismat import config as C


def cmd_cycle(args) -> int:
    from kismat.engine import run_cycle
    settings = C.Settings.load()
    report = run_cycle(settings, notify=not args.quiet)
    print(report.summary())
    if report.errors:
        print("\n".join(report.errors), file=sys.stderr)
    return 0


def cmd_backtest(args) -> int:
    from kismat.data.prices import get_daily_bars, synthetic_bars
    from kismat.strategy.backtest import BacktestConfig, run_backtest
    settings = C.Settings.load()
    universe = settings.universe
    classes = [args.asset_class] if args.asset_class else list(universe)
    bars = {}
    for cls in classes:
        for sym in universe.get(cls, []):
            try:
                bars[sym] = (synthetic_bars(args.days, seed=hash(sym) % 1000) if args.synthetic
                             else get_daily_bars(sym, cls, args.days, settings.cache_ttl_hours))
            except Exception as exc:
                print(f"skip {sym}: {exc}", file=sys.stderr)
    if not bars:
        print("no data", file=sys.stderr)
        return 1
    cfg = BacktestConfig(initial_cash=settings.risk.starting_cash, max_positions=settings.risk.max_positions,
                         max_position_pct=settings.risk.max_position_pct,
                         fee_bps=max(settings.risk.fees_bps.values()), slippage_bps=settings.risk.slippage_bps,
                         entry_threshold=settings.risk.entry_score_threshold,
                         stop_atr_multiple=settings.risk.stop_atr_multiple)
    result = run_backtest(bars, cfg)
    print(f"symbols {len(bars)} | days {result.metrics['days']}")
    print(result.summary())
    if args.json:
        print(json.dumps(result.metrics, indent=2))
    return 0


def cmd_status(args) -> int:
    from kismat.execution.paper import PaperBroker
    from kismat.journal.store import Journal
    settings = C.Settings.load()
    broker = PaperBroker(settings.risk)
    eq = Journal().read("equity", limit=1)
    print(json.dumps({"cash": broker.cash(), "positions": broker.positions(), "meta": broker.meta,
                      "last_equity": eq[-1] if eq else None}, indent=2, default=str))
    return 0


def cmd_review(args) -> int:
    from kismat.journal.review import build_review_packet
    from kismat.journal.store import Journal
    path = build_review_packet(Journal())
    print(f"review packet written: {path}")
    return 0


def cmd_approve(args) -> int:
    from kismat.engine import approve
    fills = approve(args.order_id)
    print(json.dumps(fills, indent=2))
    return 0


def cmd_reject(args) -> int:
    from kismat.engine import reject
    print(f"rejected {reject(args.order_id)} proposal(s)")
    return 0


def cmd_pending(args) -> int:
    from kismat.engine import load_pending
    print(json.dumps(load_pending(), indent=2))
    return 0


def cmd_reset_halt(args) -> int:
    from kismat.execution.paper import PaperBroker
    from kismat.journal.store import Journal
    settings = C.Settings.load()
    broker = PaperBroker(settings.risk)
    broker.meta["halted"], broker.meta["halt_reason"] = False, ""
    broker.meta["peak_equity"] = broker.equity({})
    broker.save()
    Journal().event("halt_reset", "human reset the kill switch; peak equity rebased")
    print("halt cleared")
    return 0


def cmd_validate_memos(args) -> int:
    from kismat.research.memos import load_memos
    memos = load_memos(max_age_days=3650)
    for sym, m in sorted(memos.items()):
        print(f"{sym}: {m.direction} {m.conviction:.2f} ({m.data['date']}) score={m.score():+.2f}")
    print(f"{len(memos)} valid memo(s)")
    return 0


def cmd_council(args) -> int:
    from kismat.research.packet import build_packet  # noqa: F401 (packet must exist)
    from kismat.research.runner import run_council
    settings = C.Settings.load()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY not set. Use the Claude Code routine instead (docs/RUNBOOK.md).", file=sys.stderr)
        return 2
    latest = C.RESEARCH_DIR / "packets" / "latest.json"
    if not latest.exists():
        print("no packet yet; run a cycle first", file=sys.stderr)
        return 2
    info = json.loads(latest.read_text())
    classes = C.symbol_classes(settings.universe)
    symbols = [(s, classes[s]) for s in info["candidates"][: args.limit] if s in classes]
    written = run_council(symbols, C.ROOT / info["path"])
    print(f"{len(written)} memo(s) written")
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="kismat", description="Research-first, risk-first trading lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("cycle", help="run one full cycle (paper by default)")
    s.add_argument("--quiet", action="store_true", help="skip Telegram")
    s.set_defaults(fn=cmd_cycle)
    s = sub.add_parser("backtest", help="backtest the systematic signal on the universe")
    s.add_argument("--asset-class", choices=list(C.ASSET_CLASSES))
    s.add_argument("--days", type=int, default=400)
    s.add_argument("--synthetic", action="store_true", help="offline: random-walk data")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_backtest)
    sub.add_parser("status", help="print paper account state").set_defaults(fn=cmd_status)
    sub.add_parser("review", help="build the weekly review packet").set_defaults(fn=cmd_review)
    sub.add_parser("pending", help="list proposals awaiting approval").set_defaults(fn=cmd_pending)
    s = sub.add_parser("approve", help="execute a pending proposal (id or 'all')")
    s.add_argument("order_id")
    s.set_defaults(fn=cmd_approve)
    s = sub.add_parser("reject", help="drop a pending proposal (id or 'all')")
    s.add_argument("order_id")
    s.set_defaults(fn=cmd_reject)
    sub.add_parser("reset-halt", help="clear the kill switch (human only)").set_defaults(fn=cmd_reset_halt)
    sub.add_parser("validate-memos", help="check research memos").set_defaults(fn=cmd_validate_memos)
    s = sub.add_parser("council", help="run the research council via the Claude API (needs a key)")
    s.add_argument("--limit", type=int, default=5)
    s.set_defaults(fn=cmd_council)
    args = p.parse_args(argv)
    return args.fn(args)
