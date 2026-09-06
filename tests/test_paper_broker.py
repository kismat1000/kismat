import pytest

from kismat.config import RiskLimits
from kismat.execution.paper import PaperBroker


def test_buy_sell_fees_and_persistence(tmp_path):
    lim = RiskLimits(starting_cash=1000, fees_bps={"crypto": 10}, slippage_bps=0)
    b = PaperBroker(lim, path=tmp_path / "pf.json")
    fill = b.buy("BTCUSDT", qty=1.0, price=100.0, asset_class="crypto", reason="test")
    assert fill.price == 100.0 and fill.fee == pytest.approx(0.1)
    assert b.cash() == pytest.approx(1000 - 100 - 0.1)
    assert b.equity({"BTCUSDT": 110.0}) == pytest.approx(899.9 + 110)
    b.save()
    b2 = PaperBroker(lim, path=tmp_path / "pf.json")
    assert b2.positions()["BTCUSDT"]["qty"] == 1.0
    sell = b2.sell("BTCUSDT", 1.0, 110.0, "take")
    assert sell.fee == pytest.approx(0.11)
    assert b2.positions() == {}
    assert b2.cash() == pytest.approx(899.9 + 110 - 0.11)


def test_cannot_overspend_and_liquidate(tmp_path):
    b = PaperBroker(RiskLimits(starting_cash=100, slippage_bps=0), path=tmp_path / "pf.json")
    fill = b.buy("ETHUSDT", qty=10.0, price=50.0, asset_class="crypto")
    assert fill.qty < 2.0 and b.cash() >= 0
    b.mark({"ETHUSDT": 60.0})
    assert b.meta["peak_equity"] > 100
    fills = b.liquidate_all({"ETHUSDT": 60.0}, "kill")
    assert len(fills) == 1 and b.positions() == {}
    with pytest.raises(ValueError):
        b.sell("ETHUSDT", 1, 60.0)


def test_deposit_rebases_peak_and_reset_guards(tmp_path):
    b = PaperBroker(RiskLimits(starting_cash=100), path=tmp_path / "pf.json")
    b.buy("BTCUSDT", qty=0.5, price=100.0, asset_class="crypto")
    b.mark({"BTCUSDT": 120.0})
    peak_before = b.meta["peak_equity"]
    eq = b.deposit(900.0, {"BTCUSDT": 120.0})
    assert eq == pytest.approx(b.equity({"BTCUSDT": 120.0}))
    assert b.meta["peak_equity"] == pytest.approx(eq) and eq > peak_before
    b.meta["last_entry_bar"] = {"BTCUSDT": "2026-01-01"}
    b.reset_entry_guards()
    assert b.meta["last_entry_bar"] == {}
