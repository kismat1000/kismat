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
    assert exit_rule(100, 120, 105, atr_val=5, sma_fast=110)[0]          # trailing stop 120-12.5=107.5
    assert not exit_rule(100, 120, 115, atr_val=5, sma_fast=110)[0]
    assert exit_rule(100, 100, 95, atr_val=10, sma_fast=98)[0]           # below SMA50 and underwater
    assert not exit_rule(100, 100, 99, atr_val=10, sma_fast=98)[0]


def test_exit_rule_trend_break_switch():
    assert exit_rule(100, 100, 95, atr_val=10, sma_fast=98)[0]
    assert not exit_rule(100, 100, 95, atr_val=10, sma_fast=98, trend_break=False)[0]
    assert exit_rule(100, 120, 90, atr_val=5, sma_fast=98, trend_break=False)[0]   # trailing stop still fires


def test_pattern_features_are_off_by_default_and_score_when_weighted():
    from kismat.strategy.signals import StrategyParams, add_relative_strength, compute_features, score_frame, trend_signal
    strong = synthetic_bars(400, drift=0.004, vol=0.005, seed=21)
    weak = synthetic_bars(400, drift=-0.002, vol=0.005, seed=22)
    bench = synthetic_bars(400, drift=0.001, vol=0.005, seed=23)
    off = StrategyParams()
    on = StrategyParams(w_rs=0.2, w_high=0.2, w_squeeze=0.1, benchmarks={"us_stocks": "BENCH"})
    classes = {"STRONG": "us_stocks", "WEAK": "us_stocks", "BENCH": "us_stocks"}
    feats_off = {s: compute_features(df, off) for s, df in [("STRONG", strong), ("WEAK", weak), ("BENCH", bench)]}
    feats_on = {s: compute_features(df, on) for s, df in [("STRONG", strong), ("WEAK", weak), ("BENCH", bench)]}
    add_relative_strength(feats_on, classes, on)
    assert feats_on["STRONG"]["rs"].iloc[-1] > 0 > feats_on["WEAK"]["rs"].iloc[-1]
    assert feats_on["BENCH"]["rs"].isna().all()          # the benchmark has no benchmark
    base_strong = score_frame(feats_off["STRONG"], off).iloc[-1]
    base_weak = score_frame(feats_off["WEAK"], off).iloc[-1]
    on_strong = score_frame(feats_on["STRONG"], on).iloc[-1]
    on_weak = score_frame(feats_on["WEAK"], on).iloc[-1]
    assert on_strong - base_strong > on_weak - base_weak     # relative strength rewards the leader
    assert off.min_bars == 210 and on.min_bars == 262        # the 52-week window only counts when weighted
    sig = trend_signal("STRONG", strong, 2.5, on, benchmark=bench)
    assert sig.ok and sig.features["rs"] > 0 and 0 < sig.features["near_high"] <= 1
    assert any("relative strength" in r for r in sig.reasons)
    plain = trend_signal("STRONG", strong, 2.5, off)
    assert plain.ok and plain.features["rs"] != plain.features["rs"]   # NaN without a benchmark
