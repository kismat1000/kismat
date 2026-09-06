import pytest

from kismat.config import RiskLimits
from kismat.risk.engine import OrderRequest, Portfolio, RiskEngine


def pf(**kw):
    base = dict(cash=1000.0, equity=1000.0, peak_equity=1000.0, day_start_equity=1000.0, positions={})
    base.update(kw)
    return Portfolio(**base)


def test_one_percent_risk_rule_sizes_by_stop_distance():
    eng = RiskEngine(RiskLimits(starting_cash=1000, max_position_pct=0.5))
    d = eng.size_entry(OrderRequest("BTCUSDT", "crypto", price=100.0, stop_distance=10.0), pf())
    assert d.approved
    assert d.value == pytest.approx(100.0)     # risk $10 over $10 stop -> 1 unit -> $100
    assert d.stop_price == pytest.approx(90.0)


def test_position_cap_applies():
    eng = RiskEngine(RiskLimits(starting_cash=1000, max_position_pct=0.05))
    d = eng.size_entry(OrderRequest("BTCUSDT", "crypto", price=100.0, stop_distance=1.0), pf())
    assert d.approved and d.value == pytest.approx(50.0) and "position cap" in d.reason


def test_asset_class_cap_and_max_positions():
    lim = RiskLimits(starting_cash=1000, max_positions=2, max_asset_class_pct={"crypto": 0.2})
    eng = RiskEngine(lim)
    held = {"ETHUSDT": {"qty": 1, "avg_price": 150, "asset_class": "crypto", "value": 150.0}}
    d = eng.size_entry(OrderRequest("BTCUSDT", "crypto", 100.0, 5.0), pf(positions=held, cash=850))
    assert d.approved and d.value == pytest.approx(50.0)     # 200 cap - 150 held
    held2 = dict(held, SOLUSDT={"qty": 1, "avg_price": 10, "asset_class": "crypto", "value": 10.0})
    d2 = eng.size_entry(OrderRequest("BTCUSDT", "crypto", 100.0, 5.0), pf(positions=held2))
    assert not d2.approved and "max positions" in d2.reason


def test_daily_loss_blocks_new_entries():
    eng = RiskEngine(RiskLimits(max_daily_loss_pct=0.03))
    d = eng.size_entry(OrderRequest("AAPL", "us_stocks", 100.0, 5.0), pf(equity=960.0))
    assert not d.approved and "daily loss" in d.reason


def test_kill_switch_on_drawdown():
    eng = RiskEngine(RiskLimits(max_drawdown_pct=0.10))
    assert eng.check_kill_switch(pf(equity=950))[0] is False
    hit, why = eng.check_kill_switch(pf(equity=899))
    assert hit and "kill switch" in why
    assert not eng.size_entry(OrderRequest("AAPL", "us_stocks", 100, 5), pf(halted=True, halt_reason="x")).approved


def test_dust_and_invalid_orders_rejected():
    eng = RiskEngine(RiskLimits(min_trade_value=10))
    assert not eng.size_entry(OrderRequest("X", "crypto", 100.0, 5000.0), pf()).approved
    assert not eng.size_entry(OrderRequest("X", "crypto", 0.0, 1.0), pf()).approved
    assert not eng.size_entry(OrderRequest("X", "crypto", 100.0, 1.0),
                              pf(positions={"X": {"asset_class": "crypto", "value": 1}})).approved
