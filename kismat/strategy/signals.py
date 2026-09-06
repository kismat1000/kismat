"""Systematic, explainable signals. Long-only for phase one.

Each signal returns a score in [-1, 1] and the reasons behind it, so the
journal and the dashboard can show *why* a trade happened. The research
agents' scores are merged with these in kismat.engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from kismat.strategy import indicators as ind

MIN_BARS = 210


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


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    f = pd.DataFrame(index=df.index)
    f["close"] = close
    f["sma20"] = ind.sma(close, 20)
    f["sma50"] = ind.sma(close, 50)
    f["sma200"] = ind.sma(close, 200)
    f["atr14"] = ind.atr(df, 14)
    f["atr_pct"] = f["atr14"] / close
    f["rsi14"] = ind.rsi(close, 14)
    f["roc20"] = ind.rate_of_change(close, 20)
    f["roc63"] = ind.rate_of_change(close, 63)
    f["hi55"] = ind.rolling_max(close, 55).shift(1)
    f["vol20"] = ind.realized_vol(close, 20)
    return f


def trend_signal(symbol: str, df: pd.DataFrame, stop_atr_multiple: float = 2.5) -> Signal:
    """Trend + momentum + breakout, penalised by over-extension and chaos."""
    if df is None or len(df) < MIN_BARS:
        return Signal(symbol=symbol, ok=False, reasons=[f"not enough bars ({0 if df is None else len(df)})"])
    f = compute_features(df).iloc[-1]
    if f[["sma50", "sma200", "atr14", "rsi14", "roc63", "hi55"]].isna().any():
        return Signal(symbol=symbol, ok=False, reasons=["indicators not ready"])

    score = 0.0
    reasons: list[str] = []
    close, sma50, sma200 = float(f["close"]), float(f["sma50"]), float(f["sma200"])

    # Regime: price above rising long-term averages.
    if close > sma50 > sma200:
        score += 0.35
        reasons.append("uptrend: close > SMA50 > SMA200")
    elif close < sma50 < sma200:
        score -= 0.35
        reasons.append("downtrend: close < SMA50 < SMA200")
    elif close > sma200:
        score += 0.10
        reasons.append("above SMA200 but SMA50 not aligned")
    else:
        score -= 0.10
        reasons.append("below SMA200")

    # Momentum: 3 month return, capped.
    roc63 = float(f["roc63"])
    mom = float(np.clip(roc63 / 0.30, -1, 1)) * 0.30
    score += mom
    reasons.append(f"3m momentum {roc63:+.1%}")

    # Breakout: new 55 day high.
    if close >= float(f["hi55"]):
        score += 0.20
        reasons.append("breakout: 55 day high")

    # Over-extension: RSI too hot or price far above SMA20.
    rsi = float(f["rsi14"])
    if rsi > 80:
        score -= 0.20
        reasons.append(f"overbought RSI {rsi:.0f}")
    elif rsi < 30 and close > sma200:
        score += 0.10
        reasons.append(f"pullback in uptrend RSI {rsi:.0f}")

    # Chaos filter: extreme volatility shrinks conviction.
    atr_pct = float(f["atr_pct"])
    if atr_pct > 0.08:
        score *= 0.5
        reasons.append(f"volatility filter ATR {atr_pct:.1%} of price")

    score = float(np.clip(score, -1, 1))
    atr_val = float(f["atr14"])
    return Signal(symbol=symbol, score=score, reasons=reasons, close=close, atr=atr_val,
                  stop_distance=stop_atr_multiple * atr_val,
                  features={"sma50": sma50, "sma200": sma200, "rsi14": rsi, "roc20": float(f["roc20"]),
                            "roc63": roc63, "atr_pct": atr_pct, "vol20": float(f["vol20"])})


def exit_rule(entry_price: float, highest_close: float, close: float, atr_val: float,
              sma50: float, stop_atr_multiple: float = 2.5, trend_break: bool = True) -> tuple[bool, str]:
    """Trailing ATR stop, optionally a trend break. Returns (should_exit, reason)."""
    trail = highest_close - stop_atr_multiple * atr_val
    if close <= trail:
        return True, f"trailing stop hit ({close:.4g} <= {trail:.4g})"
    if trend_break and close < sma50 and close < entry_price:
        return True, "trend break: below SMA50 and underwater"
    return False, ""
