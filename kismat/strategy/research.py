"""Walk-forward research: which parameter set survives out of sample?

A grid of parameter sets is run over the full history. The equity curve of
each is cut into consecutive windows (about six months). A set is judged by
how it did across windows, not by its total return: median window Sharpe,
share of positive windows, and the walk-forward chain, where each window is
traded with the set that was best over the windows before it.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from kismat.strategy.backtest import BacktestConfig, BacktestResult, run_backtest
from kismat.strategy.signals import StrategyParams


@dataclass
class Variant:
    name: str
    params: StrategyParams
    overrides: dict

    def config(self, base: BacktestConfig) -> BacktestConfig:
        return replace(base, params=self.params, **self.overrides)


def default_grid(quick: bool = False) -> list[Variant]:
    sma = [(50, 200), (20, 100), (100, 300)] if not quick else [(50, 200), (20, 100)]
    mom = [63, 126, 252] if not quick else [63, 126]
    stops = [2.5, 4.0]
    slots = [8, 12] if not quick else [8]
    regimes = [0.0, 0.5]
    out = []
    for (fast, slow), m, st, n, rg in itertools.product(sma, mom, stops, slots, regimes):
        name = f"sma{fast}/{slow} mom{m} stop{st} n{n}" + (f" regime{rg}" if rg else "")
        out.append(Variant(name, StrategyParams(sma_fast=fast, sma_slow=slow, mom_days=m),
                           {"stop_atr_multiple": st, "max_positions": n, "regime_breadth_min": rg}))
    return out


def window_stats(equity: pd.Series, window: int) -> list[dict]:
    stats = []
    for i in range(0, len(equity) - window + 1, window):
        seg = equity.iloc[i:i + window]
        rets = seg.pct_change().dropna()
        ret = float(seg.iloc[-1] / seg.iloc[0] - 1)
        sharpe = float(rets.mean() / rets.std() * np.sqrt(365)) if len(rets) > 2 and rets.std() > 0 else 0.0
        dd = float((seg / seg.cummax() - 1).min())
        stats.append({"start": str(seg.index[0].date()), "end": str(seg.index[-1].date()),
                      "ret": ret, "sharpe": sharpe, "max_dd": dd})
    return stats


def run_grid(bars: dict[str, pd.DataFrame], base: BacktestConfig, grid: list[Variant],
             window: int = 126) -> list[dict]:
    rows = []
    for v in grid:
        res: BacktestResult = run_backtest(bars, v.config(base))
        ws = window_stats(res.equity, window)
        sharpes = [w["sharpe"] for w in ws]
        rows.append({"name": v.name, "variant": v, "metrics": res.metrics, "windows": ws,
                     "median_window_sharpe": float(np.median(sharpes)) if sharpes else 0.0,
                     "positive_windows": sum(1 for w in ws if w["ret"] > 0) / len(ws) if ws else 0.0,
                     "worst_window": min((w["ret"] for w in ws), default=0.0)})
    return rows


def walk_forward(rows: list[dict], lookback_windows: int = 3) -> dict:
    """Trade each window with the variant that had the best mean Sharpe over the
    previous `lookback_windows` windows. Returns the chained result."""
    n = min(len(r["windows"]) for r in rows) if rows else 0
    if n <= lookback_windows:
        return {"windows": 0, "chain_return": 0.0, "picks": []}
    chain, picks = 1.0, []
    for i in range(lookback_windows, n):
        best = max(rows, key=lambda r: np.mean([w["sharpe"] for w in r["windows"][i - lookback_windows:i]]))
        w = best["windows"][i]
        chain *= 1 + w["ret"]
        picks.append({"window": f"{w['start']}..{w['end']}", "variant": best["name"], "ret": w["ret"]})
    return {"windows": n - lookback_windows, "chain_return": chain - 1, "picks": picks}


def robustness_score(r: dict) -> float:
    """Median window Sharpe, penalised for negative windows and deep drawdown."""
    return (r["median_window_sharpe"] + 0.5 * r["positive_windows"]
            + 2.0 * r["metrics"]["max_drawdown"] + 0.5 * r["worst_window"])


def report(rows: list[dict], wf: dict, path: Path, days: int, symbols: int, current: StrategyParams,
           current_cfg: BacktestConfig) -> dict:
    rows = sorted(rows, key=robustness_score, reverse=True)
    best = rows[0]
    now = datetime.now(timezone.utc)
    lines = [f"# Walk-forward research {now.date().isoformat()}", "",
             f"{symbols} symbols, {days} days requested, windows of 126 bars, {len(rows)} variants.",
             f"Current live parameters: {current.label()} stop {current_cfg.stop_atr_multiple} "
             f"n{current_cfg.max_positions} regime {current_cfg.regime_breadth_min or 'off'}.", "",
             "Ranking is by robustness (median window Sharpe, share of positive windows, drawdown,",
             "worst window), not by total return. Top 15:", "",
             "| rank | variant | return | CAGR | Sharpe | max DD | trades | windows + | median win Sharpe | worst window | robustness |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows[:15], 1):
        m = r["metrics"]
        lines.append(f"| {i} | {r['name']} | {m['total_return']:+.1%} | {m['cagr']:+.1%} | {m['sharpe']:.2f} | "
                     f"{m['max_drawdown']:.1%} | {m['trades']} | {r['positive_windows']:.0%} | "
                     f"{r['median_window_sharpe']:.2f} | {r['worst_window']:+.1%} | {robustness_score(r):.2f} |")
    lines += ["", f"## Walk-forward chain ({wf['windows']} windows, re-picked each window from the prior three)", "",
              f"- chained return {wf['chain_return']:+.1%}", ""]
    for pick in wf["picks"]:
        lines.append(f"- {pick['window']}: {pick['variant']} -> {pick['ret']:+.1%}")
    lines += ["", "## Best variant window by window", ""]
    for w in best["windows"]:
        lines.append(f"- {w['start']}..{w['end']}: {w['ret']:+.1%} (Sharpe {w['sharpe']:.2f}, DD {w['max_dd']:.1%})")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    best_json = {"generated": now.isoformat(timespec="minutes"), "name": best["name"],
                 "params": best["variant"].params.to_dict(), "overrides": best["variant"].overrides,
                 "metrics": best["metrics"], "robustness": robustness_score(best),
                 "walk_forward_chain_return": wf["chain_return"]}
    path.with_suffix(".json").write_text(json.dumps(best_json, indent=2))
    return best_json
