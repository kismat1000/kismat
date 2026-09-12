"""Deterministic headline sentiment. Cheap, explainable, and only a gate.

The council reads the news properly; this module only catches the cases where
a headline alone should stop a new entry today (fraud, investigation, hack,
bankruptcy) and gives the packet a rough per-symbol tone so the analysts see
at a glance what the tape is saying. It never adds to the score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

POSITIVE = {
    "beat", "beats", "record", "surge", "surges", "soar", "soars", "rally", "rallies", "upgrade", "upgrades",
    "raises", "raised", "growth", "strong", "profit", "profits", "buyback", "dividend", "outperform", "bullish",
    "approval", "approved", "wins", "win", "partnership", "expands", "expansion", "jumps", "gain", "gains",
    "all-time high", "breakout", "inflows", "adoption",
}
NEGATIVE = {
    "miss", "misses", "missed", "cut", "cuts", "downgrade", "downgrades", "falls", "fall", "drop", "drops",
    "plunge", "plunges", "slump", "slumps", "loss", "losses", "warning", "warns", "weak", "layoffs", "lawsuit",
    "probe", "recall", "outflows", "bearish", "selloff", "sell-off", "tumbles", "tumble", "decline", "declines",
    "delay", "delays", "halts", "halt", "fine", "fined", "penalty", "sanction", "sanctions",
}
# A single headline with one of these stops a new entry for the day.
HARD_NEGATIVE = (
    r"\bfraud\b", r"\bsec charges\b", r"\bcharged with\b", r"\bindict", r"\bbankrupt", r"\bchapter 11\b",
    r"\bdelist", r"\btrading halt", r"\bhalted\b", r"\bhack(ed|s)?\b", r"\bexploit(ed)?\b", r"\brug pull\b",
    r"\baccounting (irregularit|scandal)", r"\brestat(e|ing|ement)", r"\bgoing concern\b", r"\bsubpoena",
    r"\bcriminal (probe|investigation)\b", r"\bdoj investigation\b", r"\bceo (resigns|steps down|fired|arrested)",
)
_HARD = [re.compile(p) for p in HARD_NEGATIVE]


@dataclass
class Tone:
    symbol: str
    score: float = 0.0          # (positive - negative) / (positive + negative + 1), in (-1, 1)
    positive: int = 0
    negative: int = 0
    headlines: int = 0
    flags: list[str] = field(default_factory=list)   # hard-negative headlines, verbatim

    @property
    def vetoed(self) -> bool:
        return bool(self.flags)

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "score": round(self.score, 3), "positive": self.positive,
                "negative": self.negative, "headlines": self.headlines, "flags": self.flags}


def _words(title: str) -> set[str]:
    t = title.lower()
    return set(re.findall(r"[a-z][a-z\-]+", t)) | {p for p in POSITIVE | NEGATIVE if " " in p and p in t}


def score_headlines(symbol: str, titles: list[str]) -> Tone:
    tone = Tone(symbol=symbol, headlines=len(titles))
    for title in titles:
        words = _words(title)
        tone.positive += len(words & POSITIVE)
        tone.negative += len(words & NEGATIVE)
        low = title.lower()
        if any(rx.search(low) for rx in _HARD):
            tone.flags.append(title.strip())
    tone.score = (tone.positive - tone.negative) / (tone.positive + tone.negative + 1)
    return tone


def tone_by_symbol(headlines: list[dict], queries: dict[str, str]) -> dict[str, Tone]:
    """Group the symbol-specific headlines (those fetched with a symbol's query)
    and score each symbol. General-feed headlines carry no query and are skipped."""
    by_query: dict[str, list[str]] = {}
    for h in headlines:
        q = h.get("query") or ""
        if q:
            by_query.setdefault(q, []).append(h.get("title", ""))
    return {sym: score_headlines(sym, by_query.get(q, [])) for sym, q in queries.items()}
