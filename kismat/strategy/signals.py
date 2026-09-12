"""Systematic, explainable signals. Long-only for phase one.

Every window and weight lives in StrategyParams so the same scoring code runs
in the live engine, the backtester, and the walk-forward research harness.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from kismat.strategy import indicators as ind


@dataclass
class StrategyParams:
    sma_fast: int = 50
    sma_slow: int = 200
    mom_days: int = 63          # momentum lookback
    mom_scale: float = 0.30     # return that earns the full momentum weight
    breakout_days: int = 55
    atr_days: int = 14
    rsi_days: int = 14
    rsi_hot: float = 80.0
    rsi_cold: float = 30.0
    chaos_atr_pct: float = 0.08
    w_trend: float = 0.35
    w_misaligned: float = 0.10
    w_mom: float = 0.30
    w_breakout: float = 0.20
    w_hot: float = 0.20
    w_pullback: float = 0.10
    # Pattern features. Off at weight 0; the research feature study decides whether they earn a weight.
    high_days: int = 252         # the "52-week high" window
    high_band: float = 0.10      # full credit at the high, none this far below it
    squeeze_days: int = 100      # ATR% is compared with its median over this window
    squeeze_ratio: float = 0.75  # ATR% below this share of its median is a squeeze
    w_rs: float = 0.0            # relative strength: momentum minus the class benchmark's
    w_high: float = 0.0          # nearness to the 52-week high
    w_squeeze: float = 0.0       # volatility squeeze inside an uptrend
    benchmarks: dict = field(default_factory=dict)   # asset class -> benchmark symbol for relative strength

    @property
    def min_bars(self) -> int:
        n = max(self.sma_slow, self.mom_days, self.breakout_days)
        if self.w_high:
            n = max(n, self.high_days)
        if self.w_squeeze:
            n = max(n, self.squeeze_days + self.atr_days)
        return n + 10

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "StrategyParams":
        from kismat.config import CONFIG_DIR
        path = path or CONFIG_DIR / "strategy.yaml"
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text()) or {}
        known = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
        return cls(**known)

    def to_dict(self) -> dict:
        return asdict(self)

    def label(self) -> str:
        return f"sma{self.sma_fast}/{self.sma_slow} mom{self.mom_days} brk{self.breakout_days}"


DEFAULT_PARAMS = StrategyParams()


@dataclass
class Signal:
    symbol: str
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    close: float = float("nan")
    atr: float = float("nan")
    stop_distance: float = float("nan")
    features: dict = field(default_factory=dict)
    ok: bool = True

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "score": round(self.score, 4), "reasons": self.reasons,
                "close": self.close, "atr": self.atr, "stop_distance": self.stop_distance,
                "features": {k: (round(v, 4) if isinstance(v, float) else v)
                             for k, v in self.features.items()}, "ok": self.ok}


def compute_features(df: pd.DataFrame, p: StrategyParams = DEFAULT_PARAMS) -> pd.DataFrame:
    close = df["close"]
    f = pd.DataFrame(index=df.index)
    f["open"] = df["open"] if "open" in df else close
    f["close"] = close
    f["sma_fast"] = ind.sma(close, p.sma_fast)
    f["sma_slow"] = ind.sma(close, p.sma_slow)
    f["atr"] = ind.atr(df, p.atr_days)
    f["atr_pct"] = f["atr"] / close
    f["rsi"] = ind.rsi(close, p.rsi_days)
    f["roc20"] = ind.rate_of_change(close, 20)
    f["roc_mom"] = ind.rate_of_change(close, p.mom_days)
    f["hi_break"] = ind.rolling_max(close, p.breakout_days).shift(1)
    f["vol20"] = ind.realized_vol(close, 20)
    f["near_high"] = close / ind.rolling_max(close, p.high_days)
    f["atr_ratio"] = f["atr_pct"] / f["atr_pct"].rolling(p.squeeze_days).median()
    f["rs"] = np.nan   # relative strength needs the benchmark: see add_relative_strength
    return f


def add_relative_strength(feats: dict[str, pd.DataFrame], classes: dict[str, str] | None,
                          p: StrategyParams = DEFAULT_PARAMS) -> None:
    """Momentum minus the class benchmark's momentum, in place. Symbols without a
    benchmark in `feats` keep NaN, which scores as zero."""
    for sym, f in feats.items():
        bench = p.benchmarks.get((classes or {}).get(sym, ""))
        if bench and bench in feats and bench != sym:
            f["rs"] = f["roc_mom"] - feats[bench]["roc_mom"].reindex(f.index)


REQUIRED = ["sma_fast", "sma_slow", "atr", "rsi", "roc_mom", "hi_break"]


def score_frame(f: pd.DataFrame, p: StrategyParams = DEFAULT_PARAMS) -> pd.Series:
    """Vectorised score in [-1, 1] for every row of a feature frame (NaN when not ready)."""
    close, fast, slow = f["close"], f["sma_fast"], f["sma_slow"]
    up = (close > fast) & (fast > slow)
    down = (close < fast) & (fast < slow)
    above_slow = close > slow
    score = np.where(up, p.w_trend, np.where(down, -p.w_trend,
                     np.where(above_slow, p.w_misaligned, -p.w_misaligned))).astype(float)
    score = score + np.clip(f["roc_mom"].to_numpy() / p.mom_scale, -1, 1) * p.w_mom
    score = score + np.where(close.to_numpy() >= f["hi_break"].to_numpy(), p.w_breakout, 0.0)
    rsi = f["rsi"].to_numpy()
    score = score - np.where(rsi > p.rsi_hot, p.w_hot, 0.0)
    score = score + np.where((rsi < p.rsi_cold) & above_slow.to_numpy(), p.w_pullback, 0.0)
    if p.w_rs and "rs" in f:
        rs = np.nan_to_num(f["rs"].to_numpy(dtype=float), nan=0.0)
        score = score + np.clip(rs / p.mom_scale, -1, 1) * p.w_rs
    if p.w_high and "near_high" in f:
        nh = np.nan_to_num(f["near_high"].to_numpy(dtype=float), nan=0.0)
        score = score + np.clip((nh - (1 - p.high_band)) / p.high_band, 0, 1) * p.w_high
    if p.w_squeeze and "atr_ratio" in f:
        ar = np.nan_to_num(f["atr_ratio"].to_numpy(dtype=float), nan=9.0)
        score = score + np.where(up.to_numpy() & (ar < p.squeeze_ratio), p.w_squeeze, 0.0)
    score = np.where(f["atr_pct"].to_numpy() > p.chaos_atr_pct, score * 0.5, score)
    score = np.clip(score, -1, 1)
    ready = f[REQUIRED].notna().all(axis=1).to_numpy()
    return pd.Series(np.where(ready, score, np.nan), index=f.index, name="score")


def explain(row: pd.Series, p: StrategyParams = DEFAULT_PARAMS) -> list[str]:
    """Human-readable reasons for one feature row (the last bar, in the engine)."""
    close, fast, slow = float(row["close"]), float(row["sma_fast"]), float(row["sma_slow"])
    reasons: list[str] = []
    if close > fast > slow:
        reasons.append(f"uptrend: close > SMA{p.sma_fast} > SMA{p.sma_slow}")
    elif close < fast < slow:
        reasons.append(f"downtrend: close < SMA{p.sma_fast} < SMA{p.sma_slow}")
    elif close > slow:
        reasons.append(f"above SMA{p.sma_slow} but SMA{p.sma_fast} not aligned")
    else:
        reasons.append(f"below SMA{p.sma_slow}")
    reasons.append(f"{p.mom_days}d momentum {float(row['roc_mom']):+.1%}")
    if close >= float(row["hi_break"]):
        reasons.append(f"breakout: {p.breakout_days} day high")
    rsi = float(row["rsi"])
    if rsi > p.rsi_hot:
        reasons.append(f"overbought RSI {rsi:.0f}")
    elif rsi < p.rsi_cold and close > slow:
        reasons.append(f"pullback in uptrend RSI {rsi:.0f}")
    if p.w_rs and not pd.isna(row.get("rs", np.nan)):
        reasons.append(f"relative strength vs benchmark {float(row['rs']):+.1%}")
    if p.w_high and not pd.isna(row.get("near_high", np.nan)):
        reasons.append(f"{1 - float(row['near_high']):.1%} below the {p.high_days}-day high")
    if p.w_squeeze and not pd.isna(row.get("atr_ratio", np.nan)) and float(row["atr_ratio"]) < p.squeeze_ratio \
            and close > fast > slow:
        reasons.append(f"volatility squeeze: ATR at {float(row['atr_ratio']):.0%} of its median")
    if float(row["atr_pct"]) > p.chaos_atr_pct:
        reasons.append(f"volatility filter ATR {float(row['atr_pct']):.1%} of price")
    return reasons


def trend_signal(symbol: str, df: pd.DataFrame, stop_atr_multiple: float = 2.5,
                 p: StrategyParams = DEFAULT_PARAMS, benchmark: pd.DataFrame | None = None) -> Signal:
    """Trend + momentum + breakout, penalised by over-extension and chaos.
    `benchmark` is the class benchmark's bars, for relative strength."""
    if df is None or len(df) < p.min_bars:
        return Signal(symbol=symbol, ok=False, reasons=[f"not enough bars ({0 if df is None else len(df)})"])
    feats = compute_features(df, p)
    if p.w_rs and benchmark is not None and len(benchmark) >= p.mom_days + 1:
        feats["rs"] = feats["roc_mom"] - ind.rate_of_change(benchmark["close"], p.mom_days).reindex(feats.index)
    row = feats.iloc[-1]
    if row[REQUIRED].isna().any():
        return Signal(symbol=symbol, ok=False, reasons=["indicators not ready"])
    score = float(score_frame(feats.tail(1), p).iloc[-1])
    atr_val = float(row["atr"])
    return Signal(symbol=symbol, score=score, reasons=explain(row, p), close=float(row["close"]), atr=atr_val,
                  stop_distance=stop_atr_multiple * atr_val,
                  features={"sma_fast": float(row["sma_fast"]), "sma_slow": float(row["sma_slow"]),
                            "rsi": float(row["rsi"]), "roc20": float(row["roc20"]), "roc_mom": float(row["roc_mom"]),
                            "atr_pct": float(row["atr_pct"]), "vol20": float(row["vol20"]),
                            "near_high": float(row["near_high"]), "atr_ratio": float(row["atr_ratio"]),
                            "rs": float(row["rs"])})


def exit_rule(entry_price: float, highest_close: float, close: float, atr_val: float,
              sma_fast: float, stop_atr_multiple: float = 2.5, trend_break: bool = True) -> tuple[bool, str]:
    """Trailing ATR stop, optionally a trend break. Returns (should_exit, reason)."""
    trail = highest_close - stop_atr_multiple * atr_val
    if close <= trail:
        return True, f"trailing stop hit ({close:.4g} <= {trail:.4g})"
    if trend_break and close < sma_fast and close < entry_price:
        return True, "trend break: below fast SMA and underwater"
    return False, ""
