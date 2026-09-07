from kismat.data.prices import synthetic_bars
from kismat.strategy.backtest import BacktestConfig
from kismat.strategy.research import (Variant, default_grid, find_current, report, run_grid, verdict,
                                      walk_forward, window_stats, with_current)
from kismat.strategy.signals import StrategyParams


def _bars():
    return {f"S{i}": synthetic_bars(900, drift=d, vol=0.015, seed=100 + i)
            for i, d in enumerate([0.002, 0.001, -0.001, 0.0, 0.0015, -0.0005])}


def test_grid_walk_forward_and_report(tmp_path):
    bars = _bars()
    grid = [Variant("a", StrategyParams(), {"stop_atr_multiple": 2.5, "max_positions": 3}),
            Variant("b", StrategyParams(sma_fast=20, sma_slow=100, mom_days=126), {"stop_atr_multiple": 4.0, "max_positions": 3})]
    base = BacktestConfig(initial_cash=1000, max_positions=3)
    rows = run_grid(bars, base, grid, window=100)
    assert len(rows) == 2 and all(r["windows"] for r in rows)
    live = find_current(rows, StrategyParams(), base)
    assert live is rows[0]
    wf = walk_forward(rows, lookback_windows=2, baseline=live)
    assert wf["windows"] >= 1 and isinstance(wf["chain_return"], float) and isinstance(wf["baseline_return"], float)
    out = tmp_path / "wf.md"
    best = report(rows, wf, out, 900, len(bars), StrategyParams(), base, window=100)
    assert out.exists() and out.with_suffix(".json").exists()
    assert best["name"] in ("a", "b") and best["recommendation"] in ("keep", "consider")
    assert best["live"]["rank"] in (1, 2)
    text = out.read_text()
    assert "## Verdict" in text and "(live)" in text and "windows of 100 bars" in text
    assert len(default_grid(quick=True)) < len(default_grid())


def test_variants_share_one_start_date_so_windows_line_up():
    bars = _bars()
    grid = [Variant("short", StrategyParams(sma_fast=20, sma_slow=100), {}),
            Variant("long", StrategyParams(sma_fast=50, sma_slow=300, mom_days=252), {})]
    rows = run_grid(bars, BacktestConfig(), grid, window=100)
    assert [w["start"] for w in rows[0]["windows"]] == [w["start"] for w in rows[1]["windows"]]


def test_with_current_adds_the_live_set_when_missing():
    base = BacktestConfig(stop_atr_multiple=3.3, max_positions=7)
    grid = default_grid(quick=True)
    assert not any(v.matches(StrategyParams(), base) for v in grid)
    grown = with_current(grid, StrategyParams(), base)
    assert len(grown) == len(grid) + 1 and grown[0].matches(StrategyParams(), base)
    assert with_current(grown, StrategyParams(), base) is grown
    assert any(v.overrides.get("regime_index") for v in default_grid())


def test_verdict_keeps_unless_clearly_beaten():
    def row(name, sharpe, pos, dd, worst, oos):
        return {"name": name, "median_window_sharpe": sharpe, "positive_windows": pos, "worst_window": worst,
                "metrics": {"max_drawdown": dd, "out_of_sample_return": oos}, "windows": []}
    live = row("live", 1.0, 0.6, -0.2, -0.1, 0.10)
    close = row("close", 1.1, 0.6, -0.2, -0.1, 0.12)
    clear = row("clear", 1.6, 0.7, -0.15, -0.05, 0.20)
    wf = {"chain_return": -0.1, "baseline_return": 0.05}
    assert verdict([live, close], live, wf)["recommendation"] == "keep"
    v = verdict([close, live], live, wf)
    assert v["recommendation"] == "keep" and v["rank"] == 2 and "re-picking" in v["reason"]
    assert verdict([clear, live], live, wf)["recommendation"] == "consider"
    assert verdict([clear, live], None, wf)["recommendation"] == "keep"


def test_window_stats_shape():
    eq = synthetic_bars(400)["close"]
    ws = window_stats(eq, 100)
    assert len(ws) == 4 and all("sharpe" in w for w in ws)
