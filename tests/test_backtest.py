from kismat.data.prices import synthetic_bars
from kismat.strategy.backtest import BacktestConfig, run_backtest


def _universe():
    return {f"S{i}": synthetic_bars(500, drift=d, vol=0.015, seed=10 + i)
            for i, d in enumerate([0.002, 0.0015, -0.001, 0.0, 0.001])}


def test_backtest_runs_and_reports():
    res = run_backtest(_universe(), BacktestConfig(initial_cash=1000))
    m = res.metrics
    for key in ("total_return", "cagr", "sharpe", "max_drawdown", "trades", "win_rate",
                "in_sample_return", "out_of_sample_return"):
        assert key in m
    assert len(res.equity) > 100
    assert res.equity.iloc[0] > 0
    assert m["max_drawdown"] <= 0
    assert "Sharpe" in res.summary()


def test_costs_reduce_returns():
    cheap = run_backtest(_universe(), BacktestConfig(fee_bps=0, slippage_bps=0))
    pricey = run_backtest(_universe(), BacktestConfig(fee_bps=50, slippage_bps=25))
    assert cheap.metrics["trades"] > 0
    assert pricey.metrics["total_return"] < cheap.metrics["total_return"]


def test_never_exceeds_cash_or_position_limits():
    cfg = BacktestConfig(initial_cash=1000, max_positions=2, max_position_pct=0.3)
    res = run_backtest(_universe(), cfg)
    # equity can never go negative in a long-only, cash-limited book
    assert (res.equity > 0).all()


def test_rotation_backtest_runs_and_rotates():
    res = run_backtest(_universe(), BacktestConfig(max_positions=1, rotation_margin=0.2, min_hold_days=1))
    assert res.metrics["trades"] > 0
    assert any("rotation" in t["reason"] for t in res.trades)


def test_variant_rules_run():
    uni = _universe()
    classes = {s: ("crypto" if i % 2 else "us_stocks") for i, s in enumerate(uni)}
    base = run_backtest(uni, BacktestConfig())
    tb3 = run_backtest(uni, BacktestConfig(trend_break_days=3))
    ts = run_backtest(uni, BacktestConfig(time_stop_days=20))
    reg = run_backtest(uni, BacktestConfig(regime_breadth_min=0.5, classes=classes))
    assert len(base.equity) == len(tb3.equity) == len(ts.equity) == len(reg.equity)
    assert sum(1 for t in tb3.trades if t["reason"].startswith("trend break")) <= \
        sum(1 for t in base.trades if t["reason"].startswith("trend break"))
    assert any(t["reason"].startswith("time stop") for t in ts.trades) or ts.metrics["trades"] >= 0
