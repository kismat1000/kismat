import hashlib
import hmac
from urllib.parse import parse_qs, urlencode

import pytest

from kismat.config import RiskLimits, parse_venues
from kismat.execution import venues as V
from kismat.execution.mirror import MirrorBroker
from kismat.execution.venues import VenueFill


def test_parse_venues():
    assert parse_venues("us_stocks=alpaca,crypto=binance") == {"us_stocks": "alpaca", "crypto": "binance"}
    assert parse_venues("") == {}
    assert parse_venues("bogus=alpaca,crypto=Binance") == {"crypto": "binance"}


class _R:
    def __init__(self, status, payload=None, text=""):
        self.status_code, self._p, self.text = status, payload, text or ("x" if payload is not None else "")

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_alpaca_buy_uses_notional_and_polls_to_fill(monkeypatch):
    calls = []
    state = {"polls": 0}

    def fake_request(method, url, headers=None, timeout=None, **kw):
        calls.append((method, url, kw.get("json"), kw.get("params")))
        if method == "POST" and url.endswith("/v2/orders"):
            return _R(200, {"id": "o1", "status": "accepted"})
        if method == "GET" and "/v2/orders/o1" in url:
            state["polls"] += 1
            return _R(200, {"id": "o1", "status": "filled", "filled_qty": "0.5", "filled_avg_price": "230.1"})
        raise AssertionError(url)

    monkeypatch.setattr(V.requests, "request", fake_request)
    monkeypatch.setattr(V.time, "sleep", lambda s: None)
    a = V.AlpacaPaper("k", "s", poll_seconds=5)
    vf = a.buy("NVDA", 0.5, 230.0)
    assert vf.status == "filled" and vf.avg_price == 230.1 and vf.filled_qty == 0.5
    body = calls[0][2]
    assert body["notional"] == "115.0" and body["side"] == "buy" and body["time_in_force"] == "day"
    assert calls[0][1].startswith("https://paper-api.alpaca.markets")


def test_alpaca_sell_closes_position_and_skips_when_not_held(monkeypatch):
    def fake_request(method, url, headers=None, timeout=None, **kw):
        if method == "GET" and url.endswith("/v2/positions/NVDA"):
            return _R(200, {"symbol": "NVDA", "qty": "0.5"})
        if method == "GET" and url.endswith("/v2/positions/AAPL"):
            return _R(404)
        if method == "DELETE" and url.endswith("/v2/positions/NVDA"):
            return _R(200, {"id": "o2", "status": "filled", "filled_qty": "0.5", "filled_avg_price": "240"})
        raise AssertionError((method, url))

    monkeypatch.setattr(V.requests, "request", fake_request)
    a = V.AlpacaPaper("k", "s", poll_seconds=0)
    assert a.sell("NVDA", 0.5, 239.0).status == "filled"
    assert a.sell("AAPL", 1.0, 100.0).status == "skipped"


def test_binance_signature_and_quote_qty_buy(monkeypatch):
    captured = {}

    def fake_request(method, url, params=None, headers=None, timeout=None):
        captured.update(method=method, url=url, params=dict(params), headers=headers)
        return _R(200, {"orderId": 7, "status": "FILLED", "executedQty": "0.00125",
                        "cummulativeQuoteQty": "100.0", "fills": []})

    def fake_get(url, params=None, timeout=None):
        return _R(200, {"symbols": [{"baseAsset": "BTC", "quoteAsset": "USDT", "filters": [
            {"filterType": "LOT_SIZE", "stepSize": "0.00001"},
            {"filterType": "NOTIONAL", "minNotional": "5"}]}]})

    monkeypatch.setattr(V.requests, "request", fake_request)
    monkeypatch.setattr(V.requests, "get", fake_get)
    b = V.BinanceSpot("key", "secret", testnet=True)
    vf = b.buy("BTCUSDT", 0.00125, 80000.0)
    assert vf.status == "filled" and vf.avg_price == pytest.approx(80000.0)
    assert captured["url"].startswith("https://testnet.binance.vision") and captured["headers"]["X-MBX-APIKEY"] == "key"
    p = captured["params"]
    assert p["quoteOrderQty"] == "100.00" and p["type"] == "MARKET"
    unsigned = {k: v for k, v in p.items() if k != "signature"}
    expect = hmac.new(b"secret", urlencode(unsigned).encode(), hashlib.sha256).hexdigest()
    assert p["signature"] == expect
    assert V.BinanceSpot.round_step(0.123456, 0.001) == pytest.approx(0.123)


class _FakeVenue:
    name = "fake"

    def __init__(self, result):
        self.result, self.calls = result, []

    def ping(self): return {}
    def holds(self, symbol): return 1.0
    def open_orders(self, symbol): return 0

    def buy(self, symbol, qty, ref_price):
        self.calls.append(("buy", symbol, qty))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    def sell(self, symbol, qty, ref_price):
        self.calls.append(("sell", symbol, qty))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_mirror_books_at_venue_price_and_fails_soft(tmp_path):
    lim = RiskLimits(starting_cash=1000, slippage_bps=0, fees_bps={"crypto": 0, "us_stocks": 0})
    filled = _FakeVenue(VenueFill("filled", 1.0, 101.0, "o1", "ok"))
    b = MirrorBroker(lim, {"crypto": filled}, path=tmp_path / "pf.json")
    fill = b.buy("BTCUSDT", 1.0, 100.0, "crypto", "test")
    assert fill.price == 101.0 and "fake filled" in fill.reason and b.venue_log[0]["status"] == "filled"

    broken = _FakeVenue(RuntimeError("venue down"))
    b2 = MirrorBroker(lim, {"us_stocks": broken}, path=tmp_path / "pf2.json")
    fill2 = b2.buy("NVDA", 1.0, 200.0, "us_stocks", "test")
    assert fill2.price == 200.0 and "error" in fill2.reason and b2.positions()["NVDA"]["qty"] == 1.0

    strict = MirrorBroker(lim, {"us_stocks": broken}, strict=True, path=tmp_path / "pf3.json")
    with pytest.raises(RuntimeError):
        strict.buy("NVDA", 1.0, 200.0, "us_stocks", "test")
    assert strict.positions() == {}

    pending = _FakeVenue(VenueFill("pending", 0.0, None, "o9", "fills at open"))
    b3 = MirrorBroker(lim, {"us_stocks": pending}, path=tmp_path / "pf4.json")
    fill3 = b3.buy("MSFT", 1.0, 500.0, "us_stocks", "test")
    assert fill3.price == 500.0 and "pending" in fill3.reason
    sell = b3.sell("MSFT", 1.0, 510.0, "exit")
    assert sell.price == 510.0 and b3.positions() == {}
