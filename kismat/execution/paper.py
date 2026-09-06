"""Paper broker: fills at the given price with slippage and fees, persists to
JSON so GitHub Actions (or any stateless runner) can resume between cycles."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import RiskLimits, STATE_DIR
from kismat.execution.broker import Fill


class PaperBroker:
    name = "paper"

    def __init__(self, limits: RiskLimits, path: Path | None = None, starting_cash: float | None = None):
        self.limits = limits
        self.path = path or STATE_DIR / "paper" / "portfolio.json"
        self._cash = float(starting_cash if starting_cash is not None else limits.starting_cash)
        self._positions: dict[str, dict] = {}
        self.fills: list[Fill] = []
        self.meta: dict = {"created": _now(), "peak_equity": self._cash,
                           "halted": False, "halt_reason": "",
                           "day_start_equity": self._cash, "day_start_date": _today(),
                           "last_entry_bar": {}}
        if self.path.exists():
            self.load()

    # ---- persistence -------------------------------------------------------
    def load(self) -> None:
        raw = json.loads(self.path.read_text())
        self._cash = float(raw["cash"])
        self._positions = raw.get("positions", {})
        self.meta.update(raw.get("meta", {}))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"cash": self._cash, "positions": self._positions,
                                         "meta": self.meta, "saved": _now()}, indent=2, sort_keys=True))

    # ---- account -------------------------------------------------------------
    def cash(self) -> float:
        return self._cash

    def positions(self) -> dict[str, dict]:
        return self._positions

    def equity(self, prices: dict[str, float]) -> float:
        total = self._cash
        for sym, pos in self._positions.items():
            px = prices.get(sym, pos.get("last_price", pos["avg_price"]))
            total += pos["qty"] * px
        return total

    def mark(self, prices: dict[str, float]) -> float:
        """Update last prices, highest close and value; return equity."""
        for sym, pos in self._positions.items():
            if sym in prices:
                pos["last_price"] = prices[sym]
                pos["highest_close"] = max(pos.get("highest_close", pos["avg_price"]), prices[sym])
            pos["value"] = pos["qty"] * pos.get("last_price", pos["avg_price"])
        eq = self.equity(prices)
        self.meta["peak_equity"] = max(self.meta.get("peak_equity", eq), eq)
        today = _today()
        if self.meta.get("day_start_date") != today:
            self.meta["day_start_date"] = today
            self.meta["day_start_equity"] = eq
        return eq

    # ---- orders ----------------------------------------------------------------
    def _cost(self, asset_class: str) -> tuple[float, float]:
        return self.limits.fee_bps(asset_class) / 10_000, self.limits.slippage_bps / 10_000

    def buy(self, symbol: str, qty: float, price: float, asset_class: str, reason: str = "") -> Fill:
        fee_r, slip_r = self._cost(asset_class)
        fill_px = price * (1 + slip_r)
        gross = fill_px * qty
        fee = gross * fee_r
        if gross + fee > self._cash + 1e-9:
            qty = max(0.0, (self._cash / (1 + fee_r)) / fill_px)
            gross = fill_px * qty
            fee = gross * fee_r
        if qty <= 0:
            raise ValueError("insufficient cash")
        self._cash -= gross + fee
        if -1e-6 < self._cash < 0:
            self._cash = 0.0  # floating point dust
        pos = self._positions.get(symbol)
        if pos:
            new_qty = pos["qty"] + qty
            pos["avg_price"] = (pos["avg_price"] * pos["qty"] + fill_px * qty) / new_qty
            pos["qty"] = new_qty
        else:
            self._positions[symbol] = {"qty": qty, "avg_price": fill_px, "asset_class": asset_class,
                                       "entry_time": _now(), "highest_close": fill_px,
                                       "last_price": fill_px, "value": gross, "stop_price": None}
        fill = Fill(symbol, "buy", qty, fill_px, fee, _now(), reason)
        self.fills.append(fill)
        return fill

    def sell(self, symbol: str, qty: float, price: float, reason: str = "") -> Fill:
        pos = self._positions.get(symbol)
        if not pos:
            raise ValueError(f"no position in {symbol}")
        qty = min(qty, pos["qty"])
        fee_r, slip_r = self._cost(pos["asset_class"])
        fill_px = price * (1 - slip_r)
        gross = fill_px * qty
        fee = gross * fee_r
        self._cash += gross - fee
        pos["qty"] -= qty
        if pos["qty"] <= 1e-12:
            del self._positions[symbol]
        fill = Fill(symbol, "sell", qty, fill_px, fee, _now(), reason)
        self.fills.append(fill)
        return fill

    def deposit(self, amount: float, prices: dict[str, float] | None = None) -> float:
        """Add paper cash and rebase peak and day-start equity so drawdown math
        does not read the deposit as a gain. Returns the new equity."""
        self._cash += float(amount)
        eq = self.equity(prices or {})
        self.meta["peak_equity"] = eq
        self.meta["day_start_equity"] = eq
        return eq

    def reset_entry_guards(self) -> None:
        self.meta["last_entry_bar"] = {}
        self.meta["journal_marks"] = {}

    def liquidate_all(self, prices: dict[str, float], reason: str) -> list[Fill]:
        fills = []
        for sym in list(self._positions):
            px = prices.get(sym, self._positions[sym].get("last_price", self._positions[sym]["avg_price"]))
            fills.append(self.sell(sym, self._positions[sym]["qty"], px, reason))
        return fills


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()
