"""Append-only JSONL journal. Git-friendly, grep-friendly, no database.

decisions.jsonl : one line per symbol per cycle (what we saw, what we did, why)
fills.jsonl     : every executed order
equity.jsonl    : equity snapshot per cycle
events.jsonl    : halts, kill switches, config changes, errors
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import STATE_DIR


class Journal:
    def __init__(self, root: Path | None = None):
        self.root = root or STATE_DIR / "journal"
        self.root.mkdir(parents=True, exist_ok=True)

    def _append(self, name: str, record: dict) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
        with (self.root / f"{name}.jsonl").open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")

    def decision(self, record: dict) -> None:
        self._append("decisions", record)

    def fill(self, record: dict) -> None:
        self._append("fills", record)

    def equity(self, record: dict) -> None:
        self._append("equity", record)

    def event(self, kind: str, message: str, **extra) -> None:
        self._append("events", {"kind": kind, "message": message, **extra})

    def read(self, name: str, limit: int | None = None) -> list[dict]:
        path = self.root / f"{name}.jsonl"
        if not path.exists():
            return []
        lines = path.read_text().splitlines()
        if limit:
            lines = lines[-limit:]
        out = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out
