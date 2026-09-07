"""Walk-forward research: which parameter set survives out of sample?

A grid of parameter sets is run over the full history, every set starting on
the same day so their equity curves line up. Each curve is cut into
consecutive windows (a quarter by default). A set is judged by how it did
across windows, not by its total return: median window Sharpe, share of
positive windows, drawdown, worst window. The walk-forward chain trades each
window with the set that was best over the windows before it, and is compared
with simply holding the live parameters over the same windows: if re-picking
loses to holding, the parameters should be left alone.
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

# Index that must be above its slow SMA before a class may open new positions.
MARKET_INDEX = {"us_stocks": "SPY", "us_etfs": "SPY", "crypto": "BTCUSDT"}
VARIED = ("stop_atr_multiple", "max_positions", "regime_breadth_min", "regime_index")
SWITCH_MARGIN = 0.25   # robustness edge the top set needs before the report suggests a change


@dataclass
class Variant:
    name: str
    params: StrategyParams
    overrides: dict

    def config(self, base: BacktestConfig) -> BacktestConfig:
        return replace(base, params=self.params, **self.overrides)

    def matches(self, params: StrategyParams, cfg: BacktestConfig) -> bool:
        return self.params == params and all(
            (self.overrides.get(k) or None) == (getattr(cfg, k) or None) for k in VARIED)


def variant_name(fast: int, slow: int, mom: int, stop: float, slots: int, regime: float, market: bool) -> str:
    return (f"sma{fast}/{slow} mom{mom} stop{stop} n{slots}" + (f" regime{regime}" if regime else "")
            + (" mkt" if market else ""))


def default_grid(quick: bool = False) -> list[Variant]:
    sma = [(50, 200), (20, 100)]
    mom = [63, 126, 252] if not quick else [63, 126]
    stops = [2.5, 4.0]
    slots = [8, 12] if not quick else [8]
    regimes = [0.0, 0.5]
    markets = [False, True] if not quick else [False]
    out = []
    for (fast, slow), m, st, n, rg, mk in itertools.product(sma, mom, stops, slots, regimes, markets):
        out.append(Variant(variant_name(fast, slow, m, st, n, rg, mk),
                           StrategyParams(sma_fast=fast, sma_slow=slow, mom_days=m),
                           {"stop_atr_multiple": st, "max_positions": n, "regime_breadth_min": rg,
                            "regime_index": dict(MARKET_INDEX) if mk else None}))
    return out


def with_current(grid: list[Variant], params: StrategyParams, cfg: BacktestConfig) -> list[Variant]:
    """The live parameter set is always in the grid, so the report can rank it."""
    if any(v.matches(params, cfg) for v in grid):
        return grid
    live = Variant("live: " + params.label() + f" stop{cfg.stop_atr_multiple} n{cfg.max_positions}",
                   params, {k: getattr(cfg, k) for k in VARIED})
    return [live] + grid


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
             window: int = 63) -> list[dict]:
    # One warm-up for every variant: a set that needs 300 bars of history must not
    # get a later, easier start than a set that needs 200, or the windows drift apart.
    warmup = max([base.warmup] + [v.params.min_bars for v in grid])
    rows = []
    for v in grid:
        res: BacktestResult = run_backtest(bars, replace(v.config(base), warmup=warmup))
        ws = window_stats(res.equity, window)
        sharpes = [w["sharpe"] for w in ws]
        rows.append({"name": v.name, "variant": v, "metrics": res.metrics, "windows": ws,
                     "median_window_sharpe": float(np.median(sharpes)) if sharpes else 0.0,
                     "positive_windows": sum(1 for w in ws if w["ret"] > 0) / len(ws) if ws else 0.0,
                     "worst_window": min((w["ret"] for w in ws), default=0.0)})
    return rows


def walk_forward(rows: list[dict], lookback_windows: int = 3, baseline: dict | None = None) -> dict:
    """Trade each window with the variant that had the best mean Sharpe over the
    previous `lookback_windows` windows. Returns the chained result, and the
    return of holding `baseline` (the live set) over the same windows."""
    n = min(len(r["windows"]) for r in rows) if rows else 0
    if n <= lookback_windows:
        return {"windows": 0, "chain_return": 0.0, "baseline_return": None, "picks": []}
    chain, fixed, picks = 1.0, 1.0, []
    for i in range(lookback_windows, n):
        best = max(rows, key=lambda r: np.mean([w["sharpe"] for w in r["windows"][i - lookback_windows:i]]))
        w = best["windows"][i]
        chain *= 1 + w["ret"]
        if baseline is not None:
            fixed *= 1 + baseline["windows"][i]["ret"]
        picks.append({"window": f"{w['start']}..{w['end']}", "variant": best["name"], "ret": w["ret"]})
    return {"windows": n - lookback_windows, "chain_return": chain - 1,
            "baseline_return": fixed - 1 if baseline is not None else None, "picks": picks}


def robustness_score(r: dict) -> float:
    """Median window Sharpe, penalised for negative windows and deep drawdown."""
    return (r["median_window_sharpe"] + 0.5 * r["positive_windows"]
            + 2.0 * r["metrics"]["max_drawdown"] + 0.5 * r["worst_window"])


def find_current(rows: list[dict], params: StrategyParams, cfg: BacktestConfig) -> dict | None:
    return next((r for r in rows if r["variant"].matches(params, cfg)), None)


def verdict(ranked: list[dict], current: dict | None, wf: dict) -> dict:
    """Keep the live set unless the top set is clearly better on every axis that matters."""
    top = ranked[0]
    if current is None:
        return {"recommendation": "keep", "rank": None, "reason": "the live parameters were not in the grid"}
    rank = ranked.index(current) + 1
    edge = robustness_score(top) - robustness_score(current)
    if current is top:
        rec, why = "keep", "the live parameters are the most robust set in the grid"
    elif (edge >= SWITCH_MARGIN
          and top["metrics"]["out_of_sample_return"] > current["metrics"]["out_of_sample_return"]
          and top["positive_windows"] >= current["positive_windows"]):
        rec, why = "consider", (f"{top['name']} beats the live set by {edge:.2f} robustness with a better "
                                f"out-of-sample return and no fewer positive windows")
    else:
        rec, why = "keep", (f"the top set beats the live parameters by only {edge:.2f} robustness "
                            f"(a change needs {SWITCH_MARGIN:.2f}, a better out-of-sample return, "
                            f"and no fewer positive windows)")
    if wf.get("baseline_return") is not None and wf["chain_return"] < wf["baseline_return"]:
        why += "; re-picking parameters each window lost to holding the live set"
    return {"recommendation": rec, "rank": rank, "edge": edge, "reason": why}


def report(rows: list[dict], wf: dict, path: Path, days: int, symbols: int, current: StrategyParams,
           current_cfg: BacktestConfig, window: int = 63) -> dict:
    ranked = sorted(rows, key=robustness_score, reverse=True)
    best = ranked[0]
    cur = find_current(ranked, current, current_cfg)
    v = verdict(ranked, cur, wf)
    now = datetime.now(timezone.utc)
    lines = [f"# Walk-forward research {now.date().isoformat()}", "",
             f"{symbols} symbols, {days} days requested, windows of {window} bars, {len(rows)} variants, "
             f"all starting on the same day.",
             f"Current live parameters: {current.label()} stop {current_cfg.stop_atr_multiple} "
             f"n{current_cfg.max_positions} regime {current_cfg.regime_breadth_min or 'off'} "
             f"index filter {'on' if current_cfg.regime_index else 'off'}.", "",
             "## Verdict", "",
             f"- Recommendation: **{v['recommendation']}** ({v['reason']}).",
             f"- Live parameters rank {v['rank']} of {len(rows)} by robustness"
             + (f" (score {robustness_score(cur):.2f}, best {robustness_score(best):.2f})." if cur else "."),
             f"- Walk-forward chain (re-pick the best set each window from the prior three): "
             f"{wf['chain_return']:+.1%} over {wf['windows']} windows"
             + (f"; holding the live set over the same windows: {wf['baseline_return']:+.1%}."
                if wf.get("baseline_return") is not None else "."), "",
             "Ranking is by robustness (median window Sharpe, share of positive windows, drawdown,",
             "worst window), not by total return. Top 15:", "",
             "| rank | variant | return | CAGR | Sharpe | max DD | OOS | trades | windows + | median win Sharpe | worst window | robustness |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(ranked[:15], 1):
        m = r["metrics"]
        mark = " (live)" if r is cur else ""
        lines.append(f"| {i} | {r['name']}{mark} | {m['total_return']:+.1%} | {m['cagr']:+.1%} | {m['sharpe']:.2f} | "
                     f"{m['max_drawdown']:.1%} | {m['out_of_sample_return']:+.1%} | {m['trades']} | "
                     f"{r['positive_windows']:.0%} | {r['median_window_sharpe']:.2f} | {r['worst_window']:+.1%} | "
                     f"{robustness_score(r):.2f} |")
    if cur is not None and ranked.index(cur) >= 15:
        m = cur["metrics"]
        lines.append(f"| {v['rank']} | {cur['name']} (live) | {m['total_return']:+.1%} | {m['cagr']:+.1%} | "
                     f"{m['sharpe']:.2f} | {m['max_drawdown']:.1%} | {m['out_of_sample_return']:+.1%} | "
                     f"{m['trades']} | {cur['positive_windows']:.0%} | {cur['median_window_sharpe']:.2f} | "
                     f"{cur['worst_window']:+.1%} | {robustness_score(cur):.2f} |")
    lines += ["", f"## Walk-forward chain ({wf['windows']} windows)", ""]
    for pick in wf["picks"]:
        lines.append(f"- {pick['window']}: {pick['variant']} -> {pick['ret']:+.1%}")
    for title, row in (("Best variant window by window", best),
                       ("Live parameters window by window", cur if cur is not best else None)):
        if row is None:
            continue
        lines += ["", f"## {title}", ""]
        for w in row["windows"]:
            lines.append(f"- {w['start']}..{w['end']}: {w['ret']:+.1%} (Sharpe {w['sharpe']:.2f}, DD {w['max_dd']:.1%})")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    best_json = {"generated": now.isoformat(timespec="minutes"), "window": window, "name": best["name"],
                 "params": best["variant"].params.to_dict(), "overrides": best["variant"].overrides,
                 "metrics": best["metrics"], "robustness": robustness_score(best),
                 "walk_forward_chain_return": wf["chain_return"],
                 "live_chain_return": wf.get("baseline_return"),
                 "recommendation": v["recommendation"], "reason": v["reason"],
                 "live": {"name": cur["name"], "rank": v["rank"], "robustness": robustness_score(cur),
                          "metrics": cur["metrics"]} if cur else None}
    path.with_suffix(".json").write_text(json.dumps(best_json, indent=2))
    return best_json
