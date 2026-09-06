"""Execution venues: real broker paper environments that mirror our orders.

The ledger (cash, positions, risk) stays in the paper broker so the numbers
match the plan. A venue receives the same order and reports how it filled,
so you can see the trade in the broker's own app and we learn real fill
behaviour. A venue error never blocks the cycle in paper mode; it is journaled.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlencode

import requests

log = logging.getLogger(__name__)


@dataclass
class VenueFill:
    status: str                   # "filled", "pending", "rejected", "skipped"
    filled_qty: float = 0.0
    avg_price: float | None = None
    order_id: str = ""
    note: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in ("filled", "pending")


class Venue(Protocol):
    name: str

    def ping(self) -> dict: ...
    def holds(self, symbol: str) -> float: ...
    def open_orders(self, symbol: str) -> int: ...
    def buy(self, symbol: str, qty: float, ref_price: float) -> VenueFill: ...
    def sell(self, symbol: str, qty: float, ref_price: float) -> VenueFill: ...


# ---------------------------------------------------------------------------
ALPACA_CRYPTO = {"BTC", "ETH", "SOL", "LINK", "DOGE", "LTC", "AVAX", "XRP", "AAVE", "BCH", "DOT", "UNI",
                 "SHIB", "PEPE", "BAT", "CRV", "GRT", "MKR", "SUSHI", "XTZ", "YFI"}


def alpaca_crypto_symbol(symbol: str) -> tuple[str, str] | None:
    """BTCUSDT -> ("BTC/USD" for orders, "BTCUSD" for positions); None if Alpaca does not list it."""
    base = symbol.replace("/", "")
    for suffix in ("USDT", "USDC", "USD"):
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[:-len(suffix)]
            break
    if base not in ALPACA_CRYPTO:
        return None
    return f"{base}/USD", f"{base}USD"


class AlpacaPaper:
    """Alpaca paper trading. Market orders; notional buys, close-position sells.
    With crypto=True the same account trades Alpaca's crypto pairs 24/7."""
    name = "alpaca-paper"
    BASE = "https://paper-api.alpaca.markets"

    def __init__(self, key: str, secret: str, timeout: int = 20, poll_seconds: float = 6.0, crypto: bool = False):
        if not key or not secret:
            raise ValueError("alpaca key and secret required")
        self.h = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Content-Type": "application/json"}
        self.timeout, self.poll_seconds, self.crypto = timeout, poll_seconds, crypto
        self.name = "alpaca-paper-crypto" if crypto else "alpaca-paper"

    def _symbols(self, symbol: str) -> tuple[str, str] | None:
        """(order symbol, position symbol) or None when unsupported."""
        if not self.crypto:
            return symbol, symbol
        return alpaca_crypto_symbol(symbol)

    @property
    def _tif(self) -> str:
        return "gtc" if self.crypto else "day"

    def _req(self, method: str, path: str, **kw):
        r = requests.request(method, f"{self.BASE}{path}", headers=self.h, timeout=self.timeout, **kw)
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise RuntimeError(f"alpaca {method} {path}: {r.status_code} {r.text[:200]}")
        return r.json() if r.text else {}

    def ping(self) -> dict:
        acct = self._req("GET", "/v2/account") or {}
        clock = self._req("GET", "/v2/clock") or {}
        return {"venue": self.name, "status": acct.get("status"), "cash": acct.get("cash"),
                "equity": acct.get("equity"), "market_open": clock.get("is_open")}

    def holds(self, symbol: str) -> float:
        syms = self._symbols(symbol)
        if not syms:
            return 0.0
        pos = self._req("GET", f"/v2/positions/{syms[1]}")
        return float(pos["qty"]) if pos else 0.0

    def open_orders(self, symbol: str) -> int:
        syms = self._symbols(symbol)
        if not syms:
            return 0
        orders = self._req("GET", "/v2/orders", params={"status": "open", "symbols": syms[0]}) or []
        return len(orders)

    def cancel_open(self, symbol: str) -> int:
        syms = self._symbols(symbol)
        if not syms:
            return 0
        orders = self._req("GET", "/v2/orders", params={"status": "open", "symbols": syms[0]}) or []
        for o in orders:
            self._req("DELETE", f"/v2/orders/{o['id']}")
        return len(orders)

    def _wait(self, order: dict) -> dict:
        deadline = time.time() + self.poll_seconds
        while order.get("status") not in ("filled", "canceled", "rejected", "expired") and time.time() < deadline:
            time.sleep(1.0)
            order = self._req("GET", f"/v2/orders/{order['id']}") or order
        return order

    def _to_fill(self, order: dict, fallback_qty: float) -> VenueFill:
        status = order.get("status", "")
        if status == "filled":
            return VenueFill("filled", float(order.get("filled_qty") or fallback_qty),
                             float(order["filled_avg_price"]) if order.get("filled_avg_price") else None,
                             order.get("id", ""), "filled at alpaca", order)
        if status in ("rejected", "canceled", "expired"):
            return VenueFill("rejected", 0.0, None, order.get("id", ""), f"alpaca {status}", order)
        return VenueFill("pending", 0.0, None, order.get("id", ""),
                         f"alpaca order {status}; fills at next market open", order)

    def buy(self, symbol: str, qty: float, ref_price: float) -> VenueFill:
        syms = self._symbols(symbol)
        if not syms:
            return VenueFill("skipped", note=f"{symbol} not listed at alpaca; ledger-only")
        notional = round(qty * ref_price, 2)
        if notional < 1.0:
            return VenueFill("rejected", note="alpaca minimum notional is $1")
        order = self._req("POST", "/v2/orders", json={"symbol": syms[0], "notional": str(notional), "side": "buy",
                                                      "type": "market", "time_in_force": self._tif})
        return self._to_fill(self._wait(order), qty)

    def sell(self, symbol: str, qty: float, ref_price: float) -> VenueFill:
        syms = self._symbols(symbol)
        if not syms:
            return VenueFill("skipped", note=f"{symbol} not listed at alpaca; ledger-only exit")
        held = self.holds(symbol)
        if held <= 0:
            cancelled = self.cancel_open(symbol)
            note = "not held at alpaca; ledger-only exit" + (f"; cancelled {cancelled} queued order(s)" if cancelled else "")
            return VenueFill("skipped", note=note)
        if qty >= held * 0.999:
            order = self._req("DELETE", f"/v2/positions/{syms[1]}")   # close the whole position
        else:
            order = self._req("POST", "/v2/orders", json={"symbol": syms[0], "qty": f"{qty:.9f}".rstrip("0").rstrip("."),
                                                          "side": "sell", "type": "market", "time_in_force": self._tif})
        return self._to_fill(self._wait(order or {}), qty)


# ---------------------------------------------------------------------------
class BinanceSpot:
    """Binance spot, testnet by default. Quote-quantity market buys, step-rounded sells."""
    name = "binance-testnet"
    TESTNET = "https://testnet.binance.vision"
    LIVE = "https://api.binance.com"

    def __init__(self, key: str, secret: str, testnet: bool = True, timeout: int = 20):
        if not key or not secret:
            raise ValueError("binance key and secret required")
        self.key, self.secret = key, secret.encode()
        self.base = self.TESTNET if testnet else self.LIVE
        self.name = "binance-testnet" if testnet else "binance"
        self.timeout = timeout
        self._info: dict[str, dict] = {}

    def _signed(self, method: str, path: str, params: dict | None = None):
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 10_000
        query = urlencode(params)
        params["signature"] = hmac.new(self.secret, query.encode(), hashlib.sha256).hexdigest()
        r = requests.request(method, f"{self.base}{path}", params=params,
                             headers={"X-MBX-APIKEY": self.key}, timeout=self.timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"binance {method} {path}: {r.status_code} {r.text[:200]}")
        return r.json()

    def _public(self, path: str, params: dict | None = None):
        r = requests.get(f"{self.base}{path}", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def symbol_info(self, symbol: str) -> dict:
        if symbol not in self._info:
            info = self._public("/api/v3/exchangeInfo", {"symbol": symbol})["symbols"][0]
            step, min_notional = 0.0, 0.0
            for f in info.get("filters", []):
                if f["filterType"] == "LOT_SIZE":
                    step = float(f["stepSize"])
                if f["filterType"] in ("NOTIONAL", "MIN_NOTIONAL"):
                    min_notional = float(f.get("minNotional", 0))
            self._info[symbol] = {"base": info["baseAsset"], "quote": info["quoteAsset"],
                                  "step": step, "min_notional": min_notional}
        return self._info[symbol]

    @staticmethod
    def round_step(qty: float, step: float) -> float:
        if step <= 0:
            return qty
        return math.floor(qty / step) * step

    def ping(self) -> dict:
        acct = self._signed("GET", "/api/v3/account")
        bal = {b["asset"]: float(b["free"]) for b in acct.get("balances", []) if float(b["free"]) > 0}
        return {"venue": self.name, "can_trade": acct.get("canTrade"),
                "balances": {k: v for k, v in list(bal.items())[:8]}}

    def holds(self, symbol: str) -> float:
        base = self.symbol_info(symbol)["base"]
        acct = self._signed("GET", "/api/v3/account")
        for b in acct.get("balances", []):
            if b["asset"] == base:
                return float(b["free"])
        return 0.0

    def open_orders(self, symbol: str) -> int:
        return len(self._signed("GET", "/api/v3/openOrders", {"symbol": symbol}))

    def _to_fill(self, resp: dict) -> VenueFill:
        status = resp.get("status", "")
        executed = float(resp.get("executedQty", 0) or 0)
        quote = float(resp.get("cummulativeQuoteQty", 0) or 0)
        avg = quote / executed if executed > 0 else None
        if status == "FILLED" or (executed > 0 and status == "PARTIALLY_FILLED"):
            return VenueFill("filled", executed, avg, str(resp.get("orderId", "")), f"binance {status}", resp)
        if status in ("REJECTED", "CANCELED", "EXPIRED"):
            return VenueFill("rejected", 0.0, None, str(resp.get("orderId", "")), f"binance {status}", resp)
        return VenueFill("pending", executed, avg, str(resp.get("orderId", "")), f"binance {status}", resp)

    def buy(self, symbol: str, qty: float, ref_price: float) -> VenueFill:
        info = self.symbol_info(symbol)
        quote_qty = round(qty * ref_price, 2)
        if quote_qty < max(info["min_notional"], 1.0):
            return VenueFill("rejected", note=f"below binance minimum notional {info['min_notional']}")
        resp = self._signed("POST", "/api/v3/order", {"symbol": symbol, "side": "BUY", "type": "MARKET",
                                                       "quoteOrderQty": f"{quote_qty:.2f}",
                                                       "newOrderRespType": "FULL"})
        return self._to_fill(resp)

    def sell(self, symbol: str, qty: float, ref_price: float) -> VenueFill:
        info = self.symbol_info(symbol)
        held = self.holds(symbol)
        if held <= 0:
            return VenueFill("skipped", note="not held at binance; ledger-only exit")
        q = self.round_step(min(qty, held), info["step"])
        if q <= 0 or q * ref_price < info["min_notional"]:
            return VenueFill("rejected", note=f"quantity {q} below binance lot or notional minimum")
        resp = self._signed("POST", "/api/v3/order", {"symbol": symbol, "side": "SELL", "type": "MARKET",
                                                       "quantity": f"{q:.8f}".rstrip("0").rstrip("."),
                                                       "newOrderRespType": "FULL"})
        return self._to_fill(resp)


def build_venues(settings) -> dict[str, Venue]:
    """asset_class -> venue, from KISMAT_VENUES (e.g. 'us_stocks=alpaca,crypto=binance')."""
    out: dict[str, Venue] = {}
    for cls, name in settings.venues.items():
        try:
            if name == "alpaca":
                out[cls] = AlpacaPaper(settings.alpaca_key, settings.alpaca_secret, crypto=(cls == "crypto"))
            elif name == "binance":
                out[cls] = BinanceSpot(settings.binance_key, settings.binance_secret, testnet=not settings.is_live)
            else:
                log.warning("unknown venue %s for %s", name, cls)
        except ValueError as exc:
            log.warning("venue %s for %s not configured: %s", name, cls, exc)
    return out
