"""Command line entry points. `python -m kismat --help`."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

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
                         stop_atr_multiple=settings.risk.stop_atr_multiple,
                         rotation_margin=0.0 if args.no_rotation else settings.risk.rotation_margin,
                         min_hold_days=settings.risk.min_hold_days)
    result = run_backtest(bars, cfg)
    header = f"symbols {len(bars)} | days {result.metrics['days']} | rotation {'off' if args.no_rotation else 'on'}"
    print(header)
    print(result.summary())
    if args.json:
        print(json.dumps(result.metrics, indent=2))
    if args.report:
        from datetime import datetime, timezone
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        classes_label = args.asset_class or "all"
        by_reason = {}
        for t in result.trades:
            r = by_reason.setdefault(t["reason"].split(" (")[0].split(":")[0], {"n": 0, "pnl": 0.0})
            r["n"] += 1
            r["pnl"] += t["pnl"]
        lines = [f"## {classes_label} ({header})", "", f"- {result.summary()}",
                 f"- exits by reason: " + ", ".join(f"{k}: n={v['n']} pnl={v['pnl']:+.2f}" for k, v in by_reason.items()),
                 f"- generated {datetime.now(timezone.utc).isoformat(timespec='minutes')}", ""]
        with out.open("a") as fh:
            fh.write("\n".join(lines) + "\n")
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


def cmd_deposit(args) -> int:
    from kismat.engine import make_broker
    from kismat.journal.store import Journal
    settings = C.Settings.load()
    broker = make_broker(settings)
    eq = broker.deposit(args.amount)
    broker.save()
    Journal().event("deposit", f"paper deposit {args.amount:.2f}; equity now {eq:.2f}; peak rebased")
    print(f"deposited {args.amount:.2f}; cash {broker.cash():.2f}; equity {eq:.2f}")
    return 0


def cmd_reset_guards(args) -> int:
    from kismat.engine import make_broker
    from kismat.journal.store import Journal
    settings = C.Settings.load()
    broker = make_broker(settings)
    broker.reset_entry_guards()
    broker.save()
    Journal().event("reset_guards", "entry guards cleared; every symbol may be considered again this bar")
    print("entry guards cleared")
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


def cmd_venue_check(args) -> int:
    from kismat.execution.venues import build_venues
    settings = C.Settings.load()
    if not settings.venues:
        print("KISMAT_VENUES not set (example: us_stocks=alpaca,crypto=binance)", file=sys.stderr)
        return 2
    venues = build_venues(settings)
    ok = True
    for cls, venue in venues.items():
        try:
            print(cls, "->", json.dumps(venue.ping()))
        except Exception as exc:
            ok = False
            print(cls, "->", venue.name, "FAILED:", exc, file=sys.stderr)
    missing = set(settings.venues) - set(venues)
    if missing:
        ok = False
        print("not configured (missing keys):", ", ".join(sorted(missing)), file=sys.stderr)
    return 0 if ok else 1


def cmd_venue_sync(args) -> int:
    from kismat.engine import make_broker
    from kismat.execution.mirror import MirrorBroker
    settings = C.Settings.load()
    broker = make_broker(settings)
    if not isinstance(broker, MirrorBroker):
        print("no venues configured", file=sys.stderr)
        return 2
    prices = {s: p.get("last_price", p["avg_price"]) for s, p in broker.positions().items()}
    print(json.dumps(broker.sync_to_venues(prices), indent=2))
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
    s.add_argument("--no-rotation", action="store_true", help="disable the rotation rule for comparison")
    s.add_argument("--report", help="append a markdown summary to this file")
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
    s = sub.add_parser("deposit", help="add paper cash (test book only)")
    s.add_argument("amount", type=float)
    s.set_defaults(fn=cmd_deposit)
    sub.add_parser("reset-guards", help="clear once-per-bar entry guards").set_defaults(fn=cmd_reset_guards)
    sub.add_parser("validate-memos", help="check research memos").set_defaults(fn=cmd_validate_memos)
    sub.add_parser("venue-check", help="ping the configured broker venues").set_defaults(fn=cmd_venue_check)
    sub.add_parser("venue-sync", help="place venue orders for ledger positions the venues do not hold").set_defaults(fn=cmd_venue_sync)
    s = sub.add_parser("council", help="run the research council via the Claude API (needs a key)")
    s.add_argument("--limit", type=int, default=5)
    s.set_defaults(fn=cmd_council)
    args = p.parse_args(argv)
    return args.fn(args)
