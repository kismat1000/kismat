import numpy as np

from kismat.data.prices import synthetic_bars
from kismat.strategy import indicators as ind
from kismat.strategy.signals import exit_rule, trend_signal


def test_indicators_basic():
    df = synthetic_bars(300, seed=1)
    assert ind.sma(df["close"], 20).iloc[-1] > 0
    r = ind.rsi(df["close"], 14).dropna()
    assert ((r >= 0) & (r <= 100)).all()
    assert ind.atr(df, 14).dropna().min() >= 0
    assert ind.max_drawdown(df["close"]) <= 0


def test_uptrend_scores_positive_and_downtrend_negative():
    up = synthetic_bars(400, drift=0.003, vol=0.01, seed=2)
    down = synthetic_bars(400, drift=-0.003, vol=0.01, seed=3)
    s_up, s_down = trend_signal("UP", up), trend_signal("DOWN", down)
    assert s_up.ok and s_down.ok
    assert s_up.score > 0.35
    assert s_down.score < -0.35
    assert s_up.stop_distance > 0 and np.isfinite(s_up.atr)
    assert any("uptrend" in r for r in s_up.reasons)


def test_not_enough_bars():
    s = trend_signal("X", synthetic_bars(50))
    assert not s.ok and s.score == 0.0


def test_exit_rule():
    assert exit_rule(100, 120, 105, atr_val=5, sma50=110)[0]          # trailing stop 120-12.5=107.5
    assert not exit_rule(100, 120, 115, atr_val=5, sma50=110)[0]
    assert exit_rule(100, 100, 95, atr_val=10, sma50=98)[0]           # below SMA50 and underwater
    assert not exit_rule(100, 100, 99, atr_val=10, sma50=98)[0]
