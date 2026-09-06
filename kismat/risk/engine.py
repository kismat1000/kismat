"""The risk engine. Deterministic code that has the final say on every order.

Nothing upstream (signals, research memos, an LLM, a human in a hurry) can
bypass it. If you want different limits, edit config/risk.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from kismat.config import RiskLimits


@dataclass
class Portfolio:
    cash: float
    equity: float
    peak_equity: float
    day_start_equity: float
    positions: dict          # symbol -> {"qty", "avg_price", "asset_class", "value"}
    halted: bool = False
    halt_reason: str = ""

    def class_exposure(self, asset_class: str) -> float:
        return sum(p.get("value", 0.0) for p in self.positions.values()
                   if p.get("asset_class") == asset_class)


@dataclass
class OrderRequest:
    symbol: str
    asset_class: str
    price: float
    stop_distance: float     # entry price minus stop price, in price units
    score: float = 0.0


@dataclass
class RiskDecision:
    approved: bool
    qty: float = 0.0
    value: float = 0.0
    reason: str = ""
    stop_price: float = 0.0

    def to_dict(self) -> dict:
        return {"approved": self.approved, "qty": self.qty, "value": round(self.value, 2),
                "reason": self.reason, "stop_price": self.stop_price}


class RiskEngine:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    # ---- account level ----------------------------------------------------
    def check_kill_switch(self, pf: Portfolio) -> tuple[bool, str]:
        """True if the account must halt. Drawdown from peak beyond the limit."""
        if pf.peak_equity <= 0:
            return False, ""
        dd = pf.equity / pf.peak_equity - 1
        if dd <= -self.limits.max_drawdown_pct:
            return True, f"kill switch: drawdown {dd:.1%} beyond {self.limits.max_drawdown_pct:.0%}"
        return False, ""

    def daily_loss_breached(self, pf: Portfolio) -> tuple[bool, str]:
        if pf.day_start_equity <= 0:
            return False, ""
        loss = pf.equity / pf.day_start_equity - 1
        if loss <= -self.limits.max_daily_loss_pct:
            return True, f"daily loss {loss:.1%} beyond {self.limits.max_daily_loss_pct:.0%}: no new entries today"
        return False, ""

    # ---- order level ------------------------------------------------------
    def size_entry(self, req: OrderRequest, pf: Portfolio) -> RiskDecision:
        L = self.limits
        if pf.halted:
            return RiskDecision(False, reason=f"account halted: {pf.halt_reason}")
        if req.price <= 0 or req.stop_distance <= 0:
            return RiskDecision(False, reason="invalid price or stop distance")
        if req.symbol in pf.positions:
            return RiskDecision(False, reason="already holding")
        if len(pf.positions) >= L.max_positions:
            return RiskDecision(False, reason=f"max positions {L.max_positions} reached")
        breached, why = self.daily_loss_breached(pf)
        if breached:
            return RiskDecision(False, reason=why)

        risk_dollars = pf.equity * L.per_trade_risk_pct
        qty_by_risk = risk_dollars / req.stop_distance
        max_value = pf.equity * L.max_position_pct
        class_cap = L.max_asset_class_pct.get(req.asset_class, 1.0) * pf.equity
        class_room = class_cap - pf.class_exposure(req.asset_class)
        if class_room <= 0:
            return RiskDecision(False, reason=f"{req.asset_class} exposure cap reached")
        value = min(qty_by_risk * req.price, max_value, class_room, pf.cash)
        if value < L.min_trade_value:
            return RiskDecision(False, reason=f"order value {value:.2f} below minimum {L.min_trade_value}")
        qty = value / req.price
        stop_price = req.price - req.stop_distance
        capped_by = []
        if value < qty_by_risk * req.price - 1e-9:
            if value == max_value:
                capped_by.append("position cap")
            elif value == class_room:
                capped_by.append("asset class cap")
            elif value == pf.cash:
                capped_by.append("available cash")
        reason = "sized by 1% risk rule" if not capped_by else "capped by " + ", ".join(capped_by)
        return RiskDecision(True, qty=qty, value=value, reason=reason, stop_price=stop_price)


def new_day(last: date | None, today: date) -> bool:
    return last is None or today > last
