"""A small, honest daily backtester.

Long-only, equal-risk sizing, realistic fees and slippage, next-bar fills.
Reports the numbers that matter and a simple in-sample / out-of-sample split,
because a strategy that only works on the data it was tuned on is worthless.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from kismat.strategy.signals import compute_features, exit_rule
from kismat.strategy import indicators as ind


@dataclass
class BacktestConfig:
    initial_cash: float = 1000.0
    max_positions: int = 5
    max_position_pct: float = 0.20
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    entry_threshold: float = 0.35
    stop_atr_multiple: float = 2.5
    warmup: int = 210


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


def _score_row(row: pd.Series) -> float:
    """Same logic as signals.trend_signal, vectorised over a feature row."""
    if row[["sma50", "sma200", "atr14", "rsi14", "roc63", "hi55"]].isna().any():
        return np.nan
    close, sma50, sma200 = row["close"], row["sma50"], row["sma200"]
    score = 0.0
    if close > sma50 > sma200:
        score += 0.35
    elif close < sma50 < sma200:
        score -= 0.35
    elif close > sma200:
        score += 0.10
    else:
        score -= 0.10
    score += float(np.clip(row["roc63"] / 0.30, -1, 1)) * 0.30
    if close >= row["hi55"]:
        score += 0.20
    if row["rsi14"] > 80:
        score -= 0.20
    elif row["rsi14"] < 30 and close > sma200:
        score += 0.10
    if row["atr_pct"] > 0.08:
        score *= 0.5
    return float(np.clip(score, -1, 1))


def precompute(bars: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {}
    for sym, df in bars.items():
        f = compute_features(df)
        f["score"] = f.apply(_score_row, axis=1)
        f["open"] = df["open"]
        out[sym] = f
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


def run_backtest(bars: dict[str, pd.DataFrame], cfg: BacktestConfig | None = None) -> BacktestResult:
    cfg = cfg or BacktestConfig()
    feats = precompute(bars)
    dates = sorted(set().union(*[set(f.index) for f in feats.values()]))
    dates = dates[cfg.warmup:] if len(dates) > cfg.warmup else dates
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
            if pd.isna(row["atr14"]) or pd.isna(row["sma50"]):
                continue
            should, why = exit_rule(pos["entry"], pos["highest"], float(row["close"]),
                                    float(row["atr14"]), float(row["sma50"]), cfg.stop_atr_multiple)
            if not should and not pd.isna(row["score"]) and row["score"] < -0.10:
                should, why = True, "score turned negative"
            if should:
                pos["pending_exit"] = True
                pos["exit_reason"] = why
        open_slots = cfg.max_positions - sum(1 for p in positions.values() if not p.get("pending_exit"))
        if open_slots > 0:
            candidates = []
            for sym, f in feats.items():
                if sym in positions or day not in f.index:
                    continue
                s = f.loc[day, "score"]
                if not pd.isna(s) and s >= cfg.entry_threshold:
                    candidates.append((float(s), sym))
            candidates.sort(reverse=True)
            budget = min(mtm * cfg.max_position_pct, cash / max(open_slots, 1))
            pending_entries = {sym: budget for _, sym in candidates[:open_slots]}

    equity = pd.Series([e for _, e in equity_curve], index=[d for d, _ in equity_curve], name="equity")
    return BacktestResult(equity=equity, trades=trades, metrics=metrics_from(equity, trades))
