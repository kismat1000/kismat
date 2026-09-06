"""MirrorBroker: the paper ledger plus real venue execution.

Every buy and sell goes to the venue for its asset class first. If the venue
fills, the ledger books the trade at the venue's average price. If the venue
is pending (market closed), rejects, or errors, the ledger still books at the
reference price in paper mode and records what happened, so the cycle never
stalls and nothing is hidden. In live mode a venue failure means no fill.
"""
from __future__ import annotations

import logging
from pathlib import Path

from kismat.config import RiskLimits
from kismat.execution.broker import Fill
from kismat.execution.paper import PaperBroker
from kismat.execution.venues import Venue, VenueFill

log = logging.getLogger(__name__)


class MirrorBroker(PaperBroker):
    name = "mirror"

    def __init__(self, limits: RiskLimits, venues: dict[str, Venue], strict: bool = False,
                 path: Path | None = None, starting_cash: float | None = None):
        super().__init__(limits, path=path, starting_cash=starting_cash)
        self.venues = venues
        self.strict = strict
        self.venue_log: list[dict] = []      # what the venues said this cycle

    def venue_for(self, asset_class: str) -> Venue | None:
        return self.venues.get(asset_class)

    def _record(self, symbol: str, side: str, vf: VenueFill, venue: str) -> None:
        self.venue_log.append({"symbol": symbol, "side": side, "venue": venue, "status": vf.status,
                               "filled_qty": vf.filled_qty, "avg_price": vf.avg_price,
                               "order_id": vf.order_id, "note": vf.note})

    def has_open_order(self, symbol: str, asset_class: str) -> bool:
        venue = self.venue_for(asset_class)
        if not venue:
            return False
        try:
            return venue.open_orders(symbol) > 0
        except Exception as exc:
            log.warning("open-order check failed at %s for %s: %s", venue.name, symbol, exc)
            return False

    def buy(self, symbol: str, qty: float, price: float, asset_class: str, reason: str = "") -> Fill:
        venue = self.venue_for(asset_class)
        if venue is None:
            return super().buy(symbol, qty, price, asset_class, reason)
        try:
            vf = venue.buy(symbol, qty, price)
        except Exception as exc:
            vf = VenueFill("error", note=f"{venue.name}: {exc}")
        self._record(symbol, "buy", vf, venue.name)
        if vf.status == "filled" and vf.avg_price:
            fill = super().buy(symbol, vf.filled_qty or qty, vf.avg_price, asset_class, reason)
            fill.reason = f"{reason} | {venue.name} filled {vf.filled_qty:.6g} @ {vf.avg_price:.6g}"
            return fill
        if self.strict:
            raise RuntimeError(f"{venue.name} {vf.status}: {vf.note}")
        fill = super().buy(symbol, qty, price, asset_class, reason)  # paper: ledger still books, venue result journaled
        fill.reason = f"{reason} | {venue.name} {vf.status}: {vf.note}"
        return fill

    def sell(self, symbol: str, qty: float, price: float, reason: str = "") -> Fill:
        pos = self._positions.get(symbol)
        venue = self.venue_for(pos["asset_class"]) if pos else None
        if venue is None:
            return super().sell(symbol, qty, price, reason)
        try:
            vf = venue.sell(symbol, qty, price)
        except Exception as exc:
            vf = VenueFill("error", note=f"{venue.name}: {exc}")
        self._record(symbol, "sell", vf, venue.name)
        if vf.status == "filled" and vf.avg_price:
            fill = super().sell(symbol, qty, vf.avg_price, reason)
            fill.reason = f"{reason} | {venue.name} filled @ {vf.avg_price:.6g}"
            return fill
        if self.strict and vf.status not in ("skipped",):
            raise RuntimeError(f"{venue.name} {vf.status}: {vf.note}")
        fill = super().sell(symbol, qty, price, reason)
        fill.reason = f"{reason} | {venue.name} {vf.status}: {vf.note}"
        return fill

    def sync_to_venues(self, prices: dict[str, float]) -> list[dict]:
        """One-off: place buys at the venues for ledger positions they do not hold yet."""
        done = []
        for symbol, pos in self._positions.items():
            venue = self.venue_for(pos["asset_class"])
            if venue is None:
                continue
            try:
                held = venue.holds(symbol)
                if held > 0 or venue.open_orders(symbol) > 0:
                    done.append({"symbol": symbol, "venue": venue.name, "status": "already there", "held": held})
                    continue
                vf = venue.buy(symbol, pos["qty"], prices.get(symbol, pos.get("last_price", pos["avg_price"])))
                done.append({"symbol": symbol, "venue": venue.name, "status": vf.status, "note": vf.note,
                             "order_id": vf.order_id})
            except Exception as exc:
                done.append({"symbol": symbol, "venue": venue.name, "status": "error", "note": str(exc)})
        return done
