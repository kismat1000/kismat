"""Per-rule P&L attribution with honest error bars.

Why this exists
---------------
Between 2026-09-06 and 2026-11-09 the trend-break exit took 54 of the book's
80 exits and won **none** of them, costing -779.90 -- 61% of all realised loss.
Every weekly backtest in that period showed it. Nobody read them, because
nothing in the system ever put a rule's own record in front of a human.

The bug was found in five minutes by grouping closed trades by exit reason.
That is all this module does, so it happens every cycle instead of once a
quarter by luck.

It also refuses to over-read a small sample. Eighty trades is not many: a 10%
win rate over 80 trades has a 95% interval of roughly 5%-18%, which is a wide
enough band that "the strategy is broken" and "the strategy is unlucky" can
both sit inside it. Every rate here carries its interval, and `verdict()` only
calls a rule bad when the interval itself clears zero.
"""
from __future__ import annotations

import collections
import math
from dataclasses import dataclass, field

# A closed trade is attributed to the rule named in its exit reason.
RULES = ("trend break", "trailing stop", "score turned negative", "time stop",
         "rotation", "kill switch", "other")


def rule_of(reason: str) -> str:
    """The rule that closed a trade, from the fill's free-text reason.

    Venue notes are appended to the reason with " | ", so match on the head.
    """
    head = (reason or "").split("|")[0].strip().lower()
    for rule in RULES[:-1]:
        if rule in head:
            return rule
    return "other"


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion.

    Used instead of the normal approximation because it stays inside [0, 1] and
    behaves at the extremes -- which matters here, since the whole point is
    reporting a rule that went 0 for 54.
    """
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    lo, hi = centre - half, centre + half
    # The exact bounds at the extremes, which is where this gets read: a rule
    # that went 0-for-54 has a lower bound of exactly zero, not 7e-18 of float
    # noise, and an all-winners rule has an upper bound of exactly one.
    if successes == 0:
        lo = 0.0
    if successes == n:
        hi = 1.0
    return (max(0.0, lo), min(1.0, hi))


def mean_ci(values: list[float], z: float = 1.96) -> tuple[float, float]:
    """Normal-approximation interval for a mean. Returns (lo, hi)."""
    n = len(values)
    if n < 2:
        return (float("nan"), float("nan"))
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    half = z * math.sqrt(var / n)
    return (mean - half, mean + half)


@dataclass
class RuleRecord:
    rule: str
    pnl: float = 0.0
    trades: list[float] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t > 0)

    @property
    def win_rate(self) -> float:
        return self.wins / self.n if self.n else 0.0

    @property
    def expectancy(self) -> float:
        return self.pnl / self.n if self.n else 0.0

    def verdict(self) -> str:
        """Only calls a rule bad when the evidence clears zero.

        "losing money" needs the whole 95% interval for mean P&L per trade to
        sit below zero. Anything thinner is "too few trades to say", which is
        the honest answer most of the time.
        """
        if self.n < 10:
            return f"too few trades to say ({self.n})"
        lo, hi = mean_ci(self.trades)
        if hi < 0:
            return "LOSING MONEY: the whole 95% interval is below zero"
        if lo > 0:
            return "making money: the whole 95% interval is above zero"
        return "not distinguishable from zero"


@dataclass
class Trade:
    symbol: str
    pnl: float
    reason: str
    exit_day: str          # YYYY-MM-DD, the day the position closed


# Sells the journal cannot cost: the matching buy is missing, usually because
# it predates the journal. Counted and reported, never scored as pure profit.
_UNCOSTED: list[str] = []


def closed_trades(fills: list[dict]) -> list[Trade]:
    """FIFO-match fills into closed trades.

    Fees on both legs are included, so the P&L here is what the account felt.

    A sell with no matching buy is DROPPED, not booked. Counting its proceeds
    as profit was a real bug in this module: scoping the report to a date range
    by filtering fills cut positions off from the buys that opened them, and a
    1,079 CSL.AX exit came out as +1,077 profit. Trade matching must always see
    every fill; date scoping belongs on the matched trades, via `since`.
    """
    books: dict[str, list[list[float]]] = collections.defaultdict(list)
    out: list[Trade] = []
    _UNCOSTED.clear()
    for f in fills:
        sym = f.get("symbol")
        qty, price, fee = f.get("qty") or 0.0, f.get("price") or 0.0, f.get("fee") or 0.0
        if not sym or qty <= 0:
            continue
        if f.get("side") == "buy":
            books[sym].append([qty, price, fee])
            continue
        remaining, cost, fees = qty, 0.0, fee
        while remaining > 1e-12 and books[sym]:
            lot = books[sym][0]
            take = min(remaining, lot[0])
            cost += take * lot[1]
            if lot[0]:
                fees += lot[2] * (take / lot[0])
            lot[0] -= take
            remaining -= take
            if lot[0] <= 1e-12:
                books[sym].pop(0)
        if remaining > 1e-9:
            # No cost basis for some or all of this sell: we cannot say what it
            # earned, so it is not a data point.
            _UNCOSTED.append(sym)
            continue
        out.append(Trade(sym, qty * price - cost - fees, f.get("reason", ""),
                         str(f.get("ts") or "")[:10]))
    return out


def uncosted() -> list[str]:
    """Symbols whose exits had no matching buy in the last `closed_trades` run."""
    return list(_UNCOSTED)


def since(trades: list[Trade], day: str | None) -> list[Trade]:
    """Closed trades that exited on `day` (YYYY-MM-DD) or later.

    Scoping matters: the 57 trend-break losses are permanent history, so a
    report over all time is red forever and stops being a signal. Pointing
    this at the date a fix landed asks the only useful question -- is the rule
    still losing money *now*.

    This takes matched trades, never raw fills, so a position opened before
    `day` and closed after it keeps its real cost basis.
    """
    if not day:
        return trades
    return [t for t in trades if t.exit_day >= day]


def by_rule(trades: list[Trade]) -> dict[str, RuleRecord]:
    records: dict[str, RuleRecord] = {}
    for t in trades:
        pnl, reason = t.pnl, t.reason
        rule = rule_of(reason)
        rec = records.setdefault(rule, RuleRecord(rule))
        rec.pnl += pnl
        rec.trades.append(pnl)
    return records


def divergences(fills: list[dict]) -> int:
    """Exits the ledger recorded that the broker did not actually execute.

    Every one of these is a position the account thinks it closed and the
    broker still holds, so the equity curve is fiction until they are
    reconciled. Counted loudly rather than logged quietly.
    """
    bad = ("ledger-only", "error:", "not held at", "not listed at")
    return sum(1 for f in fills
               if f.get("side") == "sell" and any(b in (f.get("reason") or "") for b in bad))


def losing_rules(trades: list[Trade]) -> list[RuleRecord]:
    """Rules whose entire 95% interval for P&L per trade sits below zero."""
    return [r for r in by_rule(trades).values() if r.verdict().startswith("LOSING")]


def report(trades: list[Trade], equity: list[dict] | None = None,
           fills: list[dict] | None = None) -> str:
    records = by_rule(trades)
    pnls = [p for r in records.values() for p in r.trades]
    lines = []

    if not pnls:
        # Still report the warnings. A bare "nothing to attribute" while exits
        # were failing at the venue would bury the most important fact on the
        # page.
        head = ["No closed trades to attribute."]
        if uncosted():
            head.append(f"NOTE: {len(uncosted())} exit(s) had no matching buy in the "
                        f"journal ({', '.join(sorted(set(uncosted())))}); cost basis "
                        f"unknown, so they are not data points.")
        div0 = divergences(fills) if fills else 0
        if div0:
            head.append(f"WARNING: {div0} exits were ledger-only or failed at the "
                        f"venue. Until `venue-check` reconciles them, the ledger is "
                        f"bookkeeping, not broker-confirmed fact.")
        return "\n".join(head)

    total = sum(pnls)
    wins = sum(1 for p in pnls if p > 0)
    wlo, whi = wilson(wins, len(pnls))
    lines.append(f"Closed trades: {len(pnls)}   realised: {total:+.2f}")
    lines.append(f"Win rate: {wins / len(pnls):.0%}  (95% CI {wlo:.0%}-{whi:.0%})")
    if len(pnls) >= 2:
        elo, ehi = mean_ci(pnls)
        lines.append(f"Per trade: {total / len(pnls):+.2f}  (95% CI {elo:+.2f} to {ehi:+.2f})")
    else:
        lines.append(f"Per trade: {total / len(pnls):+.2f}  "
                     f"(no interval: one trade says nothing)")
    lines.append("")
    lines.append("By the rule that closed the trade, worst first:")
    for rec in sorted(records.values(), key=lambda r: r.pnl):
        lo, hi = wilson(rec.wins, rec.n)
        lines.append(f"  {rec.rule:<22} n={rec.n:<4} pnl={rec.pnl:+10.2f}  "
                     f"per trade {rec.expectancy:+8.2f}  "
                     f"wins {rec.wins}/{rec.n} ({rec.win_rate:.0%}, CI {lo:.0%}-{hi:.0%})")
        lines.append(f"  {'':<22} -> {rec.verdict()}")

    losing = [r for r in records.values() if r.verdict().startswith("LOSING")]
    if losing:
        lines.append("")
        lines.append("ACT ON THIS: these rules are losing money beyond sampling error.")
        for r in losing:
            lines.append(f"  {r.rule}: {r.pnl:+.2f} over {r.n} trades, "
                         f"{r.wins} winners. Turn it off or fix it.")

    missing = uncosted()
    if missing:
        lines.append("")
        lines.append(f"NOTE: {len(missing)} exit(s) had no matching buy in the journal "
                     f"({', '.join(sorted(set(missing)))}) and were left out. "
                     f"Their cost basis is unknown, so they are not data points.")

    div = divergences(fills) if fills else 0
    if div:
        lines.append("")
        lines.append(f"WARNING: {div} exits were ledger-only or failed at the venue. "
                     f"Until `venue-check` reconciles them, the numbers above are "
                     f"bookkeeping, not broker-confirmed fact.")

    if equity:
        first, last = equity[0], equity[-1]
        eq, peak = last.get("equity"), last.get("peak")
        if eq and peak:
            lines.append("")
            lines.append(f"Equity {eq:,.2f}  peak {peak:,.2f}  "
                         f"drawdown {(eq / peak - 1) * 100:+.1f}%  "
                         f"since {str(first.get('ts'))[:10]}")
            lines.append("Judge this against the strategy's own window distribution, not "
                         "against zero: its backtest loses money in 43% of 10-week windows "
                         "and the median 10-week return is only +1.2%. Ten weeks is noise.")
    return "\n".join(lines)
