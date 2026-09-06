"""Broker interface. Paper broker today; Alpaca, Binance, IBKR adapters later.

Every adapter must implement this surface so the engine never cares which
one it is talking to.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Fill:
    symbol: str
    side: str            # "buy" or "sell"
    qty: float
    price: float         # average fill price after slippage
    fee: float
    timestamp: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "side": self.side, "qty": self.qty, "price": self.price,
                "fee": round(self.fee, 6), "timestamp": self.timestamp, "reason": self.reason}


class Broker(Protocol):
    name: str

    def cash(self) -> float: ...
    def positions(self) -> dict[str, dict]: ...
    def buy(self, symbol: str, qty: float, price: float, asset_class: str, reason: str = "") -> Fill: ...
    def sell(self, symbol: str, qty: float, price: float, reason: str = "") -> Fill: ...
    def save(self) -> None: ...
