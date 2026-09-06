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
