import pandas as pd
import pytest
import requests

from kismat.data import prices


def test_crypto_to_yahoo_mapping():
    assert prices.crypto_to_yahoo("BTCUSDT") == "BTC-USD"
    assert prices.crypto_to_yahoo("SOLUSDC") == "SOL-USD"
    assert prices.crypto_to_yahoo("ETHUSD") == "ETH-USD"
    assert prices.crypto_to_yahoo("BTC-USD") == "BTC-USD"


class _Resp:
    def __init__(self, status, rows=None):
        self.status_code, self._rows = status, rows or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self):
        return self._rows


def test_binance_falls_through_hosts_then_yahoo(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        if "binance.com" in url:
            return _Resp(451)
        rows = [[1_700_000_000_000 + i * 86_400_000, "1", "2", "0.5", "1.5", "100"] for i in range(3)]
        return _Resp(200, rows)

    monkeypatch.setattr(prices.requests, "get", fake_get)
    df = prices.fetch_binance_daily("BTCUSDT", 3)
    assert len(df) == 3 and list(df.columns) == prices.COLUMNS
    assert any("binance.com" in c for c in calls) and any("binance.us" in c for c in calls)

    monkeypatch.setattr(prices.requests, "get", lambda *a, **k: _Resp(451))
    monkeypatch.setattr(prices, "fetch_yahoo_daily",
                        lambda sym, days: pd.DataFrame({c: [1.0] for c in prices.COLUMNS},
                                                       index=pd.to_datetime(["2026-01-01"], utc=True)).assign(symbol=sym))
    df = prices.fetch_crypto_daily("ETHUSDT", 3)
    assert df["symbol"].iloc[0] == "ETH-USD"

    monkeypatch.setattr(prices, "fetch_yahoo_daily", lambda sym, days: (_ for _ in ()).throw(ValueError("down")))
    with pytest.raises(ValueError):
        prices.fetch_crypto_daily("ETHUSDT", 3)
