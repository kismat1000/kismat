"""Research memos: structured opinions written by the research agents.

A memo is a JSON file at research/memos/<YYYY-MM-DD>/<SYMBOL>.json that
follows prompts/memo_schema.json. The engine turns memos into a research
score in [-1, 1] that decays with age, and treats a high-conviction "avoid"
as a veto on new entries.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from kismat.config import RESEARCH_DIR

log = logging.getLogger(__name__)

REQUIRED = ("symbol", "asset_class", "date", "direction", "conviction", "thesis",
            "bull_case", "bear_case", "catalysts", "risks", "invalidation",
            "horizon_days", "sources", "agent")
DIRECTIONS = ("long", "flat", "avoid")


@dataclass
class Memo:
    data: dict
    path: Path

    @property
    def symbol(self) -> str:
        return self.data["symbol"]

    @property
    def date(self) -> date:
        return date.fromisoformat(self.data["date"])

    @property
    def direction(self) -> str:
        return self.data["direction"]

    @property
    def conviction(self) -> float:
        return float(self.data["conviction"])

    def age_days(self, today: date | None = None) -> int:
        today = today or datetime.now(timezone.utc).date()
        return (today - self.date).days

    def score(self, today: date | None = None, max_age_days: int = 5) -> float:
        """+conviction for long, -conviction for avoid, 0 for flat, decaying
        linearly to zero at max_age_days."""
        age = self.age_days(today)
        if age < 0 or age > max_age_days:
            return 0.0
        decay = 1 - age / (max_age_days + 1)
        sign = {"long": 1.0, "avoid": -1.0, "flat": 0.0}[self.direction]
        return sign * self.conviction * decay

    def vetoes_entry(self, today: date | None = None, max_age_days: int = 5,
                     min_conviction: float = 0.7) -> bool:
        return (self.direction == "avoid" and self.conviction >= min_conviction
                and 0 <= self.age_days(today) <= max_age_days)


def validate(data: dict) -> list[str]:
    errors = []
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if data["direction"] not in DIRECTIONS:
        errors.append(f"direction must be one of {DIRECTIONS}")
    try:
        c = float(data["conviction"])
        if not 0 <= c <= 1:
            errors.append("conviction must be within 0..1")
    except (TypeError, ValueError):
        errors.append("conviction must be a number")
    try:
        date.fromisoformat(data["date"])
    except (TypeError, ValueError):
        errors.append("date must be YYYY-MM-DD")
    for key in ("catalysts", "risks", "sources"):
        if not isinstance(data[key], list):
            errors.append(f"{key} must be a list")
    if not isinstance(data["horizon_days"], int) or data["horizon_days"] < 1:
        errors.append("horizon_days must be a positive integer")
    return errors


def memo_dir(root: Path | None = None) -> Path:
    return (root or RESEARCH_DIR) / "memos"


def load_memos(root: Path | None = None, max_age_days: int = 5,
               today: date | None = None) -> dict[str, Memo]:
    """Latest valid memo per symbol, ignoring anything older than max_age_days."""
    today = today or datetime.now(timezone.utc).date()
    latest: dict[str, Memo] = {}
    base = memo_dir(root)
    if not base.exists():
        return latest
    for path in sorted(base.glob("*/*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            log.warning("bad memo %s: %s", path, exc)
            continue
        errs = validate(data)
        if errs:
            log.warning("invalid memo %s: %s", path, "; ".join(errs))
            continue
        memo = Memo(data, path)
        if not 0 <= memo.age_days(today) <= max_age_days:
            continue
        prev = latest.get(memo.symbol)
        if prev is None or memo.date >= prev.date:
            latest[memo.symbol] = memo
    return latest


def write_memo(data: dict, root: Path | None = None) -> Path:
    errs = validate(data)
    if errs:
        raise ValueError("; ".join(errs))
    target = memo_dir(root) / data["date"]
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{data['symbol']}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return path
