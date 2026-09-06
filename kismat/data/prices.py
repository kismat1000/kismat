"""Free daily price data with a local cache.

crypto     -> Binance public klines (no key, generous limits)
us_stocks  -> Yahoo Finance via yfinance
au_stocks  -> Yahoo Finance via yfinance (".AX" symbols)

Every fetch is cached to data_cache/<symbol>.csv. If the network is down the
stale cache is used, with a warning, so a flaky API never crashes a cycle.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from kismat.config import CACHE_DIR

log = logging.getLogger(__name__)

# Binance.com answers HTTP 451 from US networks (GitHub Actions runners are
# US-based). Try the global host, then Binance.US, then Yahoo as a last resort.
BINANCE_HOSTS = ("https://api.binance.com", "https://api.binance.us")
COLUMNS = ["open", "high", "low", "close", "volume"]
QUOTE_SUFFIXES = ("USDT", "USDC", "USD")


def _cache_path(symbol: str) -> Path:
    safe = symbol.replace("/", "_").replace("=", "_")
    return CACHE_DIR / f"{safe}.csv"


def _read_cache(symbol: str, ttl_hours: float | None) -> pd.DataFrame | None:
    path = _cache_path(symbol)
    if not path.exists():
        return None
    if ttl_hours is not None:
        age_h = (time.time() - path.stat().st_mtime) / 3600
        if age_h > ttl_hours:
            return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True)
        return df[COLUMNS].astype(float)
    except Exception as exc:  # corrupt cache: ignore it
        log.warning("cache read failed for %s: %s", symbol, exc)
        return None


def _write_cache(symbol: str, df: pd.DataFrame) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_cache_path(symbol))


def fetch_binance_daily(symbol: str, lookback_days: int,
                        hosts: tuple[str, ...] = BINANCE_HOSTS) -> pd.DataFrame:
    limit = min(1000, lookback_days + 5)
    last_exc: Exception | None = None
    for host in hosts:
        try:
            resp = requests.get(f"{host}/api/v3/klines",
                                params={"symbol": symbol, "interval": "1d", "limit": limit},
                                timeout=20)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                raise ValueError(f"no klines for {symbol} at {host}")
            idx = pd.to_datetime([r[0] for r in rows], unit="ms", utc=True)
            data = np.array([[r[1], r[2], r[3], r[4], r[5]] for r in rows], dtype=float)
            df = pd.DataFrame(data, index=idx, columns=COLUMNS)
            df.index.name = "date"
            return df
        except Exception as exc:
            last_exc = exc
            log.warning("binance host %s failed for %s: %s", host, symbol, exc)
    raise last_exc if last_exc else ValueError(f"no binance host for {symbol}")


def crypto_to_yahoo(symbol: str) -> str:
    """BTCUSDT -> BTC-USD. Yahoo quotes every major coin in USD."""
    if "-" in symbol:
        return symbol  # already a Yahoo symbol
    for suffix in QUOTE_SUFFIXES:
        if symbol.endswith(suffix) and len(symbol) > len(suffix):
            return f"{symbol[:-len(suffix)]}-USD"
    return symbol


def fetch_crypto_daily(symbol: str, lookback_days: int) -> pd.DataFrame:
    try:
        return fetch_binance_daily(symbol, lookback_days)
    except Exception as exc:
        log.warning("binance unavailable for %s (%s); falling back to yahoo", symbol, exc)
        return fetch_yahoo_daily(crypto_to_yahoo(symbol), lookback_days)


def fetch_yahoo_daily(symbol: str, lookback_days: int) -> pd.DataFrame:
    import yfinance as yf  # imported lazily: slow import, optional in tests

    start = (datetime.now(timezone.utc) - timedelta(days=lookback_days + 10)).date()
    raw = yf.download(symbol, start=str(start), interval="1d",
                      auto_adjust=True, progress=False, threads=False)
    if raw is None or raw.empty:
        raise ValueError(f"no yahoo data for {symbol}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [c[0] for c in raw.columns]
    raw = raw.rename(columns=str.lower)
    df = raw[COLUMNS].astype(float).dropna()
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "date"
    return df


def get_daily_bars(symbol: str, asset_class: str, lookback_days: int = 400,
                   cache_ttl_hours: float = 6.0) -> pd.DataFrame:
    """Daily OHLCV bars, newest last. Uses cache first, network second,
    stale cache as the last resort."""
    cached = _read_cache(symbol, cache_ttl_hours)
    if cached is not None and len(cached) >= min(lookback_days, 200):
        return cached
    try:
        if asset_class == "crypto":
            df = fetch_crypto_daily(symbol, lookback_days)
        else:
            df = fetch_yahoo_daily(symbol, lookback_days)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        _write_cache(symbol, df)
        return df
    except Exception as exc:
        stale = _read_cache(symbol, ttl_hours=None)
        if stale is not None:
            log.warning("using stale cache for %s after fetch error: %s", symbol, exc)
            return stale
        raise


def get_fx_rate(pair: str = "AUDUSD", cache_ttl_hours: float = 12.0,
                fallback: float = 0.65) -> float:
    """Spot FX from Yahoo (e.g. AUDUSD=X). Falls back to a static rate so a
    missing quote never blocks a cycle."""
    symbol = f"{pair}=X"
    try:
        df = get_daily_bars(symbol, "us_stocks", lookback_days=10,
                            cache_ttl_hours=cache_ttl_hours)
        rate = float(df["close"].iloc[-1])
        if rate > 0:
            return rate
    except Exception as exc:
        log.warning("fx fetch failed for %s: %s (using %.4f)", pair, exc, fallback)
    return fallback


def synthetic_bars(days: int = 400, start_price: float = 100.0, drift: float = 0.0005,
                   vol: float = 0.02, seed: int = 0) -> pd.DataFrame:
    """Deterministic random-walk bars for tests and offline demos."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, size=days)
    close = start_price * np.cumprod(1 + rets)
    high = close * (1 + np.abs(rng.normal(0, vol / 2, size=days)))
    low = close * (1 - np.abs(rng.normal(0, vol / 2, size=days)))
    open_ = np.concatenate([[start_price], close[:-1]])
    volume = rng.uniform(1e5, 1e6, size=days)
    end = pd.Timestamp.now(tz="UTC").normalize()
    idx = pd.date_range(end=end, periods=days, freq="D")
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                       "volume": volume}, index=idx)
    df.index.name = "date"
    return df
