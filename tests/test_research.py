from pathlib import Path

from kismat.data.prices import synthetic_bars
from kismat.strategy.backtest import BacktestConfig
from kismat.strategy.research import Variant, default_grid, report, run_grid, walk_forward, window_stats
from kismat.strategy.signals import StrategyParams


def test_grid_walk_forward_and_report(tmp_path):
    bars = {f"S{i}": synthetic_bars(900, drift=d, vol=0.015, seed=100 + i)
            for i, d in enumerate([0.002, 0.001, -0.001, 0.0, 0.0015, -0.0005])}
    grid = [Variant("a", StrategyParams(), {"stop_atr_multiple": 2.5, "max_positions": 3}),
            Variant("b", StrategyParams(sma_fast=20, sma_slow=100, mom_days=126), {"stop_atr_multiple": 4.0, "max_positions": 3})]
    rows = run_grid(bars, BacktestConfig(initial_cash=1000), grid, window=100)
    assert len(rows) == 2 and all(r["windows"] for r in rows)
    wf = walk_forward(rows, lookback_windows=2)
    assert wf["windows"] >= 1 and isinstance(wf["chain_return"], float)
    out = tmp_path / "wf.md"
    best = report(rows, wf, out, 900, len(bars), StrategyParams(), BacktestConfig())
    assert out.exists() and out.with_suffix(".json").exists()
    assert best["name"] in ("a", "b")
    assert len(default_grid(quick=True)) < len(default_grid())


def test_window_stats_shape():
    eq = synthetic_bars(400)["close"]
    ws = window_stats(eq, 100)
    assert len(ws) == 4 and all("sharpe" in w for w in ws)
