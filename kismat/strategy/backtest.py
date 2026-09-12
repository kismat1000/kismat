"""A small, honest daily backtester.

Long-only, equal-risk sizing, realistic fees and slippage, next-bar fills.
Reports the numbers that matter and a simple in-sample / out-of-sample split,
because a strategy that only works on the data it was tuned on is worthless.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from kismat.strategy.signals import (DEFAULT_PARAMS, StrategyParams, add_relative_strength, compute_features,
                                     exit_rule, score_frame)
from kismat.strategy import indicators as ind
from kismat.data.events import in_blackout


@dataclass
class BacktestConfig:
    initial_cash: float = 1000.0
    max_positions: int = 5
    max_position_pct: float = 0.20
    risk_per_trade: float = 0.0        # size so a stop-out loses this share of equity (0 = fixed fraction only)
    class_caps: dict | None = None     # asset class -> max share of equity, as the live risk engine enforces
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    entry_threshold: float = 0.35
    stop_atr_multiple: float = 2.5
    warmup: int = 210
    rotation_margin: float = 0.0
    min_hold_days: int = 1
    trend_break_exit: bool = True
    trend_break_days: int = 1
    time_stop_days: int = 0
    regime_breadth_min: float = 0.0
    regime_index: dict | None = None   # asset class -> index symbol; entries only while it closes above its slow SMA
    earnings: dict | None = None       # symbol -> list of earnings dates (datetime.date)
    earnings_blackout_days: int = 0    # no entry this many calendar days before an earnings date
    classes: dict | None = None        # symbol -> asset class, for the regime filters
    params: StrategyParams = field(default_factory=StrategyParams)


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def summary(self) -> str:
        m = self.metrics
        return (f"return {m['total_return']:+.1%} | CAGR {m['cagr']:+.1%} | "
                f"Sharpe {m['sharpe']:.2f} | max DD {m['max_drawdown']:.1%} | "
                f"trades {m['trades']} | win rate {m['win_rate']:.0%} | "
                f"IS {m['in_sample_return']:+.1%} / OOS {m['out_of_sample_return']:+.1%}")


def precompute(bars: dict[str, pd.DataFrame], p: StrategyParams = DEFAULT_PARAMS,
               classes: dict | None = None) -> dict[str, pd.DataFrame]:
    out = {sym: compute_features(df, p) for sym, df in bars.items()}
    add_relative_strength(out, classes, p)
    for f in out.values():
        f["score"] = score_frame(f, p)
    return out


def metrics_from(equity: pd.Series, trades: list[dict]) -> dict:
    rets = equity.pct_change().dropna()
    days = max(len(equity), 1)
    total = float(equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 1 else 0.0
    years = days / 365.0
    cagr = float((1 + total) ** (1 / years) - 1) if years > 0 and total > -1 else 0.0
    sharpe = float(rets.mean() / rets.std() * np.sqrt(365)) if len(rets) > 2 and rets.std() > 0 else 0.0
    wins = [t for t in trades if t["pnl"] > 0]
    half = len(equity) // 2
    is_ret = float(equity.iloc[half] / equity.iloc[0] - 1) if half > 0 else 0.0
    oos_ret = float(equity.iloc[-1] / equity.iloc[half] - 1) if half > 0 else 0.0
    return {
        "total_return": total, "cagr": cagr, "sharpe": sharpe,
        "max_drawdown": ind.max_drawdown(equity), "trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "avg_win": float(np.mean([t["pnl_pct"] for t in wins])) if wins else 0.0,
        "avg_loss": float(np.mean([t["pnl_pct"] for t in trades if t["pnl"] <= 0]))
        if len(trades) > len(wins) else 0.0,
        "in_sample_return": is_ret, "out_of_sample_return": oos_ret,
        "days": days,
    }


def breadth_by_class(feats: dict[str, pd.DataFrame], classes: dict | None) -> dict[str, pd.Series]:
    """Share of each class's symbols closing above their SMA200, per day."""
    groups: dict[str, list[pd.Series]] = {}
    for sym, f in feats.items():
        cls = (classes or {}).get(sym, "all")
        groups.setdefault(cls, []).append((f["close"] > f["sma_slow"]).astype(float).where(f["sma_slow"].notna()))
    return {cls: pd.concat(series, axis=1).mean(axis=1) for cls, series in groups.items()}


def index_regime(feats: dict[str, pd.DataFrame], regime_index: dict | None) -> dict[str, pd.Series]:
    """Per asset class: 1.0 on days its index closed above its slow SMA, 0.0 below, NaN before warm-up."""
    out = {}
    for cls, idx in (regime_index or {}).items():
        if idx in feats:
            f = feats[idx]
            out[cls] = (f["close"] > f["sma_slow"]).astype(float).where(f["sma_slow"].notna())
    return out


def run_backtest(bars: dict[str, pd.DataFrame], cfg: BacktestConfig | None = None) -> BacktestResult:
    cfg = cfg or BacktestConfig()
    feats = precompute(bars, cfg.params, cfg.classes)
    breadth = breadth_by_class(feats, cfg.classes) if cfg.regime_breadth_min > 0 else {}
    index_ok = index_regime(feats, cfg.regime_index)
    warmup = max(cfg.warmup, cfg.params.min_bars)
    dates = sorted(set().union(*[set(f.index) for f in feats.values()]))
    dates = dates[warmup:] if len(dates) > warmup else dates
    cash = cfg.initial_cash
    positions: dict[str, dict] = {}
    trades: list[dict] = []
    equity_curve = []
    cost = (cfg.fee_bps + cfg.slippage_bps) / 10_000
    pending_entries: dict[str, float] = {}

    for day in dates:
        # 1. Fill yesterday's decisions at today's open.
        for sym, pos in list(positions.items()):
            if pos.get("pending_exit") and day in feats[sym].index:
                px = float(feats[sym].loc[day, "open"]) * (1 - cost)
                pnl = (px - pos["entry"]) * pos["qty"]
                cash += px * pos["qty"]
                trades.append({"symbol": sym, "entry_date": pos["entry_date"], "exit_date": day,
                               "entry": pos["entry"], "exit": px, "qty": pos["qty"], "pnl": pnl,
                               "pnl_pct": px / pos["entry"] - 1, "reason": pos["exit_reason"]})
                del positions[sym]
        for sym, value in pending_entries.items():
            if sym in positions or day not in feats[sym].index:
                continue
            px = float(feats[sym].loc[day, "open"]) * (1 + cost)
            qty = value / px
            if qty * px > cash:
                continue
            cash -= qty * px
            positions[sym] = {"entry": px, "qty": qty, "entry_date": day, "highest": px}
        pending_entries = {}

        # 2. Mark to market at close.
        mtm = cash
        for sym, pos in positions.items():
            if day in feats[sym].index:
                c = float(feats[sym].loc[day, "close"])
                pos["highest"] = max(pos["highest"], c)
                pos["last_close"] = c
            mtm += pos.get("last_close", pos["entry"]) * pos["qty"]
        equity_curve.append((day, mtm))

        # 3. Decide for tomorrow.
        for sym, pos in positions.items():
            if day not in feats[sym].index:
                continue
            row = feats[sym].loc[day]
            if pd.isna(row["atr"]) or pd.isna(row["sma_fast"]):
                continue
            should, why = exit_rule(pos["entry"], pos["highest"], float(row["close"]),
                                    float(row["atr"]), float(row["sma_fast"]), cfg.stop_atr_multiple,
                                    cfg.trend_break_exit)
            if should and why.startswith("trend break"):
                pos["below"] = pos.get("below", 0) + 1
                if pos["below"] < cfg.trend_break_days:
                    should, why = False, ""
            elif not should:
                pos["below"] = 0
            if not should and cfg.time_stop_days > 0 and (day - pos["entry_date"]).days >= cfg.time_stop_days \
                    and float(row["close"]) < pos["entry"]:
                should, why = True, f"time stop: underwater after {cfg.time_stop_days} days"
            if not should and not pd.isna(row["score"]) and row["score"] < -0.10:
                should, why = True, "score turned negative"
            if should:
                pos["pending_exit"] = True
                pos["exit_reason"] = why
        candidates = []
        for sym, f in feats.items():
            if sym in positions or day not in f.index:
                continue
            s = f.loc[day, "score"]
            if pd.isna(s) or s < cfg.entry_threshold:
                continue
            if breadth:
                cls = (cfg.classes or {}).get(sym, "all")
                b = breadth.get(cls)
                if b is not None and day in b.index and not pd.isna(b.loc[day]) and b.loc[day] < cfg.regime_breadth_min:
                    continue
            if index_ok:
                ok = index_ok.get((cfg.classes or {}).get(sym, "all"))
                if ok is not None and day in ok.index and not pd.isna(ok.loc[day]) and ok.loc[day] < 0.5:
                    continue
            if cfg.earnings_blackout_days > 0 and cfg.earnings and sym in cfg.earnings:
                # the fill is at tomorrow's open, so the blackout is measured from tomorrow
                if in_blackout(cfg.earnings[sym], day.date(), cfg.earnings_blackout_days + 1):
                    continue
            candidates.append((float(s), sym))
        candidates.sort(reverse=True)
        open_slots = cfg.max_positions - sum(1 for p in positions.values() if not p.get("pending_exit"))
        if open_slots <= 0 and cfg.rotation_margin > 0 and candidates:
            best_score, best_sym = candidates[0]
            held = []
            for sym, pos in positions.items():
                if pos.get("pending_exit") or day not in feats[sym].index:
                    continue
                age = (day - pos["entry_date"]).days
                sc = feats[sym].loc[day, "score"]
                if age >= cfg.min_hold_days and not pd.isna(sc):
                    held.append((float(sc), sym))
            if held:
                weak_score, weak_sym = min(held)
                if best_score - weak_score >= cfg.rotation_margin:
                    positions[weak_sym]["pending_exit"] = True
                    positions[weak_sym]["exit_reason"] = f"rotation into {best_sym}"
                    open_slots = 1
        if open_slots > 0:
            budget = min(mtm * cfg.max_position_pct, cash / max(open_slots, 1)) if cash > 0 else mtm * cfg.max_position_pct
            exposure: dict[str, float] = {}
            for sym, pos in positions.items():
                if not pos.get("pending_exit"):
                    cls = (cfg.classes or {}).get(sym, "all")
                    exposure[cls] = exposure.get(cls, 0.0) + pos.get("last_close", pos["entry"]) * pos["qty"]
            for _, sym in candidates:
                if len(pending_entries) >= open_slots:
                    break
                value = budget
                row = feats[sym].loc[day]
                if cfg.risk_per_trade > 0 and not pd.isna(row["atr"]) and row["close"] > 0:
                    # Same rule as the live risk engine: qty = equity * risk / stop distance.
                    stop_pct = cfg.stop_atr_multiple * float(row["atr"]) / float(row["close"])
                    if stop_pct > 0:
                        value = min(value, mtm * cfg.risk_per_trade / stop_pct)
                cls = (cfg.classes or {}).get(sym, "all")
                if cfg.class_caps and cls in cfg.class_caps:
                    value = min(value, cfg.class_caps[cls] * mtm - exposure.get(cls, 0.0))
                if value < 1.0:
                    continue
                pending_entries[sym] = value
                exposure[cls] = exposure.get(cls, 0.0) + value

    equity = pd.Series([e for _, e in equity_curve], index=[d for d, _ in equity_curve], name="equity")
    return BacktestResult(equity=equity, trades=trades, metrics=metrics_from(equity, trades))
