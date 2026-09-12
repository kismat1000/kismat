"""Scheduled events that move single names: earnings dates.

Free from Yahoo Finance via yfinance, cached as JSON with a daily TTL. Every
failure returns an empty list: no earnings data must never stop a cycle, and
the risk rule that reads it treats "unknown" as "no blackout".
"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

from kismat.config import CACHE_DIR

log = logging.getLogger(__name__)
EARNINGS_CLASSES = ("us_stocks", "au_stocks")


def _cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"earnings_{symbol.replace('/', '_').replace('.', '_')}.json"


def _read_cache(symbol: str, ttl_hours: float) -> list[date] | None:
    p = _cache_path(symbol)
    if not p.exists() or ttl_hours <= 0:
        return None
    if time.time() - p.stat().st_mtime > ttl_hours * 3600:
        return None
    try:
        return [date.fromisoformat(d) for d in json.loads(p.read_text())]
    except Exception:
        return None


def fetch_earnings_dates(symbol: str, limit: int = 60) -> list[date]:
    """Past and upcoming earnings dates from Yahoo, oldest first."""
    import yfinance as yf
    frame = yf.Ticker(symbol).get_earnings_dates(limit=limit)
    if frame is None or len(frame) == 0:
        return []
    out = set()
    for ts in frame.index:
        try:
            out.add(ts.date() if hasattr(ts, "date") else datetime.fromisoformat(str(ts)).date())
        except Exception:
            continue
    return sorted(out)


def earnings_dates(symbol: str, asset_class: str, cache_ttl_hours: float = 24.0) -> list[date]:
    if asset_class not in EARNINGS_CLASSES:
        return []
    cached = _read_cache(symbol, cache_ttl_hours)
    if cached is not None:
        return cached
    try:
        dates = fetch_earnings_dates(symbol)
    except Exception as exc:
        log.warning("earnings dates for %s unavailable: %s", symbol, exc)
        return []
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(symbol).write_text(json.dumps([d.isoformat() for d in dates]))
    except Exception:
        pass
    return dates


def in_blackout(dates: list[date], today: date, days_before: int) -> date | None:
    """The earnings date that falls within `days_before` calendar days ahead of
    `today` (inclusive of the day itself), or None."""
    if days_before <= 0:
        return None
    for d in dates:
        if 0 <= (d - today).days <= days_before:
            return d
    return None
