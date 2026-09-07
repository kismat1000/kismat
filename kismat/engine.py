"""One trading cycle, start to finish.

    data -> signals -> research merge -> risk engine -> paper broker
         -> journal -> research packet -> alerts -> dashboard

Every dependency with a network behind it is injectable so the whole cycle
runs offline in tests.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from kismat import config as C
from kismat.alerts import telegram
from kismat.dashboard import build as dashboard
from kismat.data import news, prices as price_data
from kismat.execution.mirror import MirrorBroker
from kismat.execution.paper import PaperBroker
from kismat.execution.venues import build_venues
from kismat.journal.store import Journal
from kismat.research import memos as memo_store
from kismat.research.packet import build_packet
from kismat.risk.engine import OrderRequest, Portfolio, RiskEngine
from kismat.strategy.signals import Signal, compute_features, exit_rule, trend_signal

log = logging.getLogger(__name__)

RESEARCH_WEIGHT = 0.4
BarsProvider = Callable[[str, str], pd.DataFrame]


@dataclass
class CycleReport:
    equity: float = 0.0
    cash: float = 0.0
    drawdown: float = 0.0
    halted: bool = False
    fills: list[dict] = field(default_factory=list)
    proposals: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    signals: dict[str, dict] = field(default_factory=dict)
    packet_path: Path | None = None
    dashboard_path: Path | None = None

    def summary(self) -> str:
        lines = [f"Kismat cycle {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                 f"equity {self.equity:,.2f} | cash {self.cash:,.2f} | drawdown {self.drawdown:.2%}"
                 + (" | HALTED" if self.halted else "")]
        for f in self.fills:
            lines.append(f"{f['side'].upper()} {f['symbol']} qty {f['qty']:.6g} @ {f['price']:.6g}: {f['reason']}")
        for p in self.proposals:
            lines.append(f"PROPOSED buy {p['symbol']} value {p['value']:.2f} @ {p['price']:.6g} (id {p['id']})")
        if not self.fills and not self.proposals:
            lines.append("no trades this cycle")
        if self.errors:
            lines.append(f"errors: {len(self.errors)} (see state/journal/events.jsonl)")
        return "\n".join(lines)


def make_broker(settings: C.Settings) -> PaperBroker:
    """Paper ledger, mirrored to real venues when KISMAT_VENUES is set."""
    venues = build_venues(settings) if settings.venues else {}
    if venues:
        return MirrorBroker(settings.risk, venues, strict=settings.is_live)
    return PaperBroker(settings.risk)


def combined_score(systematic: float, research: float | None) -> float:
    if research is None:
        return systematic
    return (1 - RESEARCH_WEIGHT) * systematic + RESEARCH_WEIGHT * research


def _latest_bar_date(df: pd.DataFrame) -> str:
    return str(df.index[-1].date())


def _held_days(pos: dict) -> float:
    try:
        entered = datetime.fromisoformat(pos["entry_time"])
    except (KeyError, ValueError):
        return 0.0
    return (datetime.now(timezone.utc) - entered).total_seconds() / 86400


def _first_time(broker: PaperBroker, key: str, stamp: str) -> bool:
    """True the first time (key, stamp) is seen; used to journal routine
    hold/skip decisions once per bar instead of once per cycle."""
    marks = broker.meta.setdefault("journal_marks", {})
    if marks.get(key) == stamp:
        return False
    marks[key] = stamp
    return True


def run_cycle(settings: C.Settings | None = None, *, bars_provider: BarsProvider | None = None,
              headlines_provider: Callable[[dict[str, str]], list[dict]] | None = None,
              fx_provider: Callable[[], float] | None = None, broker: PaperBroker | None = None,
              journal: Journal | None = None, memos_root: Path | None = None,
              docs_dir: Path | None = None, notify: bool = True) -> CycleReport:
    settings = settings or C.Settings.load()
    C.ensure_dirs()
    limits = settings.risk
    broker = broker or make_broker(settings)
    journal = journal or Journal()
    if isinstance(broker, MirrorBroker):
        broker.venue_log.clear()
    risk = RiskEngine(limits)
    report = CycleReport()
    classes = C.symbol_classes(settings.universe)
    bars_provider = bars_provider or (lambda s, cls: price_data.get_daily_bars(
        s, cls, settings.lookback_days, settings.cache_ttl_hours))
    fx = None

    if settings.is_live:
        journal.event("warning", "live mode requested but no live broker adapter is wired yet; running paper")

    # 1. Data and signals ------------------------------------------------------
    bars: dict[str, pd.DataFrame] = {}
    signals: dict[str, Signal] = {}
    latest_price: dict[str, float] = {}
    for symbol, cls in classes.items():
        try:
            df = bars_provider(symbol, cls)
            if cls == "au_stocks":
                if fx is None:
                    fx = (fx_provider or price_data.get_fx_rate)()
                df = df * 1.0
                for col in ("open", "high", "low", "close"):
                    df[col] = df[col] * fx
            bars[symbol] = df
            sig = trend_signal(symbol, df, limits.stop_atr_multiple, settings.strategy)
            signals[symbol] = sig
            latest_price[symbol] = float(df["close"].iloc[-1])
        except Exception as exc:
            msg = f"data error {symbol}: {exc}"
            report.errors.append(msg)
            journal.event("error", msg)
            log.warning(msg)
    report.signals = {s: sig.to_dict() for s, sig in signals.items()}
    native_prices: dict[str, float] = {}
    if fx:
        if _first_time(broker, "fx", datetime.now(timezone.utc).date().isoformat()):
            journal.event("fx", f"AUDUSD {fx:.4f} used to convert ASX prices to USD")
        native_prices = {s: latest_price[s] / fx for s, cls in classes.items()
                         if cls == "au_stocks" and s in latest_price}

    # 1b. Regime breadth per asset class (share of symbols above SMA200) -----------
    breadth: dict[str, float] = {}
    if limits.regime_breadth_min > 0:
        counts: dict[str, list[float]] = {}
        for symbol, sig in signals.items():
            if sig.ok and sig.features.get("sma_slow"):
                counts.setdefault(classes[symbol], []).append(1.0 if sig.close > sig.features["sma_slow"] else 0.0)
        breadth = {cls: sum(v) / len(v) for cls, v in counts.items() if v}

    # 2. Research memos ----------------------------------------------------------
    memos = memo_store.load_memos(memos_root)
    research_scores = {s: m.score() for s, m in memos.items()}

    # 3. Mark to market, kill switch, daily loss --------------------------------
    equity = broker.mark(latest_price)
    peak = broker.meta.get("peak_equity", equity)
    drawdown = equity / peak - 1 if peak else 0.0
    pf = Portfolio(cash=broker.cash(), equity=equity, peak_equity=peak,
                   day_start_equity=broker.meta.get("day_start_equity", equity),
                   positions=broker.positions(), halted=broker.meta.get("halted", False),
                   halt_reason=broker.meta.get("halt_reason", ""))
    kill, why = risk.check_kill_switch(pf)
    if kill and not pf.halted:
        fills = broker.liquidate_all(latest_price, why)
        for f in fills:
            journal.fill(f.to_dict())
            report.fills.append(f.to_dict())
        broker.meta["halted"], broker.meta["halt_reason"] = True, why
        pf.halted, pf.halt_reason = True, why
        journal.event("kill_switch", why)
        equity = broker.mark(latest_price)
    report.halted = pf.halted

    # 4. Exits ------------------------------------------------------------------
    held_scores: dict[str, float] = {}
    last_entry_bar = broker.meta.setdefault("last_entry_bar", {})
    if not pf.halted:
        for symbol, pos in list(broker.positions().items()):
            if symbol not in bars:
                continue
            sig = signals[symbol]
            f = compute_features(bars[symbol], settings.strategy).iloc[-1]
            price = latest_price[symbol]
            research = research_scores.get(symbol)
            combined = combined_score(sig.score, research)
            should, reason = (False, "")
            if sig.ok and not pd.isna(f["atr"]) and not pd.isna(f["sma_fast"]):
                should, reason = exit_rule(pos["avg_price"], pos.get("highest_close", pos["avg_price"]),
                                           price, float(f["atr"]), float(f["sma_fast"]), limits.stop_atr_multiple,
                                           limits.trend_break_exit)
                bar_date = _latest_bar_date(bars[symbol])
                if should and reason.startswith("trend break"):
                    if pos.get("below_bar") != bar_date:          # count once per bar
                        pos["below_bar"] = bar_date
                        pos["below_bars"] = pos.get("below_bars", 0) + 1
                    if pos["below_bars"] < limits.trend_break_days:
                        should, reason = False, ""
                elif not should:
                    pos["below_bars"] = 0
                if (not should and limits.time_stop_days > 0 and _held_days(pos) >= limits.time_stop_days
                        and price < pos["avg_price"]):
                    should, reason = True, f"time stop: underwater after {limits.time_stop_days} days"
            if not should and combined < limits.exit_score_threshold:
                should, reason = True, f"combined score {combined:+.2f} below exit threshold"
            if not should and symbol in memos and memos[symbol].vetoes_entry():
                should, reason = True, f"research veto: {memos[symbol].data['thesis'][:80]}"
            record = {"symbol": symbol, "systematic": round(sig.score, 3),
                      "research": round(research, 3) if research is not None else None,
                      "combined": round(combined, 3), "price": price, "held": True}
            held_scores[symbol] = combined
            if should:
                last_entry_bar[symbol] = _latest_bar_date(bars[symbol])  # no re-entry on the bar we exit
                try:
                    fill = broker.sell(symbol, pos["qty"], price, reason)
                except Exception as exc:
                    msg = f"sell {symbol} failed: {exc}"
                    journal.event("error", msg)
                    report.errors.append(msg)
                    record.update(action="sell-failed", reason=msg)
                    journal.decision(record)
                    report.decisions.append(record)
                    continue
                journal.fill(fill.to_dict())
                report.fills.append(fill.to_dict())
                record.update(action="sell", reason=fill.reason)
            else:
                record.update(action="hold", reason="; ".join(sig.reasons[:2]))
            if should or _first_time(broker, f"hold:{symbol}", _latest_bar_date(bars[symbol])):
                journal.decision(record)
            report.decisions.append(record)

    # 5. Entries ------------------------------------------------------------------
    equity = broker.mark(latest_price)
    pf = Portfolio(cash=broker.cash(), equity=equity, peak_equity=broker.meta.get("peak_equity", equity),
                   day_start_equity=broker.meta.get("day_start_equity", equity),
                   positions=broker.positions(), halted=broker.meta.get("halted", False),
                   halt_reason=broker.meta.get("halt_reason", ""))
    candidates = []
    for symbol, sig in signals.items():
        if not sig.ok or symbol in broker.positions():
            continue
        research = research_scores.get(symbol)
        combined = combined_score(sig.score, research)
        vetoed = symbol in memos and memos[symbol].vetoes_entry()
        if breadth and breadth.get(classes[symbol], 1.0) < limits.regime_breadth_min:
            continue  # asset class is in a downtrend regime
        if combined >= limits.entry_score_threshold and not vetoed:
            candidates.append((combined, symbol, research))
    candidates.sort(reverse=True)

    # 4b. Rotation: book full, a much stronger candidate is waiting ------------------
    if (not pf.halted and limits.rotation_margin > 0 and candidates
            and len(broker.positions()) >= limits.max_positions):
        best_score, best_symbol, _ = candidates[0]
        if last_entry_bar.get(best_symbol) != _latest_bar_date(bars[best_symbol]):
            eligible = [(held_scores.get(s, 0.0), s) for s, p in broker.positions().items()
                        if _held_days(p) >= limits.min_hold_days and s in latest_price]
            if eligible:
                weak_score, weak_symbol = min(eligible)
                if best_score - weak_score >= limits.rotation_margin:
                    reason = (f"rotation: {best_symbol} scores {best_score:+.2f} vs {weak_symbol} "
                              f"{weak_score:+.2f}, margin {limits.rotation_margin:.2f}")
                    last_entry_bar[weak_symbol] = _latest_bar_date(bars[weak_symbol])
                    try:
                        fill = broker.sell(weak_symbol, broker.positions()[weak_symbol]["qty"],
                                           latest_price[weak_symbol], reason)
                        journal.fill(fill.to_dict())
                        report.fills.append(fill.to_dict())
                        rec = {"symbol": weak_symbol, "systematic": None, "research": None,
                               "combined": round(weak_score, 3), "price": latest_price[weak_symbol],
                               "held": True, "action": "sell", "reason": fill.reason}
                        journal.decision(rec)
                        report.decisions.append(rec)
                        equity = broker.mark(latest_price)
                        pf = Portfolio(cash=broker.cash(), equity=equity, peak_equity=pf.peak_equity,
                                       day_start_equity=pf.day_start_equity, positions=broker.positions())
                    except Exception as exc:
                        msg = f"rotation sell {weak_symbol} failed: {exc}"
                        journal.event("error", msg)
                        report.errors.append(msg)

    for combined, symbol, research in candidates:
        sig = signals[symbol]
        bar_date = _latest_bar_date(bars[symbol])
        record = {"symbol": symbol, "systematic": round(sig.score, 3),
                  "research": round(research, 3) if research is not None else None,
                  "combined": round(combined, 3), "price": sig.close, "held": False}
        if last_entry_bar.get(symbol) == bar_date:
            continue  # already decided on this bar
        if isinstance(broker, MirrorBroker) and broker.has_open_order(symbol, classes[symbol]):
            record.update(action="skip", reason="order already open at venue")
            journal.decision(record)
            report.decisions.append(record)
            continue
        req = OrderRequest(symbol=symbol, asset_class=classes[symbol], price=sig.close,
                           stop_distance=sig.stop_distance, score=combined)
        decision = risk.size_entry(req, pf)
        if not decision.approved:
            record.update(action="skip", reason=decision.reason)
            if _first_time(broker, f"skip:{symbol}", f"{bar_date}:{decision.reason[:24]}"):
                journal.decision(record)   # journal each distinct reason once per bar
            report.decisions.append(record)
            continue                       # not stamped: a freed slot lets it enter this bar
        last_entry_bar[symbol] = bar_date
        reason = "; ".join(sig.reasons[:3]) + (f"; research {research:+.2f}" if research is not None else "")
        if settings.approval_mode:
            proposal = {"id": uuid.uuid4().hex[:8], "symbol": symbol, "asset_class": classes[symbol],
                        "qty": decision.qty, "value": decision.value, "price": sig.close,
                        "stop_price": decision.stop_price, "reason": reason,
                        "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            _append_pending(proposal)
            report.proposals.append(proposal)
            record.update(action="proposed", reason=reason)
        else:
            try:
                fill = broker.buy(symbol, decision.qty, sig.close, classes[symbol], reason)
            except Exception as exc:
                msg = f"buy {symbol} failed: {exc}"
                journal.event("error", msg)
                report.errors.append(msg)
                record.update(action="buy-failed", reason=msg)
                journal.decision(record)
                report.decisions.append(record)
                continue
            if symbol in broker.positions():
                broker.positions()[symbol]["stop_price"] = decision.stop_price
            journal.fill(fill.to_dict())
            report.fills.append(fill.to_dict())
            record.update(action="buy", reason=f"{fill.reason} | {decision.reason}")
            pf = Portfolio(cash=broker.cash(), equity=broker.mark(latest_price), peak_equity=pf.peak_equity,
                           day_start_equity=pf.day_start_equity, positions=broker.positions())
        journal.decision(record)
        report.decisions.append(record)

    # 6. Snapshot, packet, alerts, dashboard ----------------------------------------
    equity = broker.mark(latest_price)
    peak = broker.meta.get("peak_equity", equity)
    drawdown = equity / peak - 1 if peak else 0.0
    report.equity, report.cash, report.drawdown = equity, broker.cash(), drawdown
    journal.equity({"equity": round(equity, 2), "cash": round(broker.cash(), 2), "drawdown": round(drawdown, 4),
                    "peak": round(peak, 2), "positions": len(broker.positions()), "halted": report.halted})
    broker.save()
    if isinstance(broker, MirrorBroker):
        for v in broker.venue_log:
            journal.event("venue", f"{v['side']} {v['symbol']} at {v['venue']}: {v['status']} {v['note']}", **v)

    top = sorted(signals.values(), key=lambda s: -s.score)
    packet_symbols = [s.symbol for s in top[:10] if s.ok] + [s for s in broker.positions() if s in signals]
    packet_symbols = list(dict.fromkeys(packet_symbols))
    try:
        queries = {s: news.default_query_for(s, classes[s]) for s in packet_symbols[:8]}
        headlines = (headlines_provider(queries) if headlines_provider
                     else [h.to_dict() for h in news.fetch_headlines(queries)])
        news_dir = C.RESEARCH_DIR / "news"
        news_dir.mkdir(parents=True, exist_ok=True)
        (news_dir / f"{datetime.now(timezone.utc).date().isoformat()}.json").write_text(
            json.dumps({"count": len(headlines), "items": headlines}, indent=1))
    except Exception as exc:
        headlines = []
        report.errors.append(f"news error: {exc}")
        journal.event("error", f"news error: {exc}")
    report.packet_path = build_packet(report.signals, broker.positions(), headlines,
                                      {s: m.data for s, m in memos.items()}, equity, broker.cash(),
                                      packet_symbols, memos_root, fx=fx, native_prices=native_prices)
    if notify and (report.fills or report.proposals or report.halted):
        telegram.send(report.summary(), settings.telegram_bot_token, settings.telegram_chat_id)
    report.dashboard_path = dashboard.build(journal, broker, memos, report.signals, settings, docs_dir)
    return report


# ---- approval mode helpers ---------------------------------------------------------
def _pending_path() -> Path:
    return C.STATE_DIR / "pending_orders.json"


def _append_pending(proposal: dict) -> None:
    items = load_pending()
    items.append(proposal)
    _pending_path().write_text(json.dumps(items, indent=2))


def load_pending() -> list[dict]:
    p = _pending_path()
    return json.loads(p.read_text()) if p.exists() else []


def approve(order_id: str, settings: C.Settings | None = None, broker: PaperBroker | None = None,
            journal: Journal | None = None) -> list[dict]:
    settings = settings or C.Settings.load()
    broker = broker or PaperBroker(settings.risk)
    journal = journal or Journal()
    items = load_pending()
    chosen = [i for i in items if order_id == "all" or i["id"] == order_id]
    done = []
    for p in chosen:
        try:
            fill = broker.buy(p["symbol"], p["qty"], p["price"], p["asset_class"], "approved: " + p["reason"])
            broker.positions()[p["symbol"]]["stop_price"] = p["stop_price"]
            journal.fill(fill.to_dict())
            journal.decision({"symbol": p["symbol"], "action": "buy", "reason": "human approved " + p["id"],
                              "price": p["price"], "combined": None, "systematic": None, "research": None})
            done.append(fill.to_dict())
        except Exception as exc:
            journal.event("error", f"approve {p['id']} failed: {exc}")
    remaining = [i for i in items if i not in chosen]
    _pending_path().write_text(json.dumps(remaining, indent=2))
    broker.save()
    return done


def reject(order_id: str) -> int:
    items = load_pending()
    remaining = [i for i in items if not (order_id == "all" or i["id"] == order_id)]
    _pending_path().write_text(json.dumps(remaining, indent=2))
    return len(items) - len(remaining)
