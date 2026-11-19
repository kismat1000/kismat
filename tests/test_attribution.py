import math

import pytest

from kismat.research.attribution import (RuleRecord, Trade, by_rule,
                                         closed_trades, divergences, mean_ci,
                                         report, rule_of, since, uncosted,
                                         wilson)


def buy(sym, qty, price, fee=0.0, day="2026-01-01"):
    return {"symbol": sym, "side": "buy", "qty": qty, "price": price,
            "fee": fee, "ts": f"{day}T00:00:00+00:00"}


def sell(sym, qty, price, reason, fee=0.0, day="2026-01-02"):
    return {"symbol": sym, "side": "sell", "qty": qty, "price": price,
            "fee": fee, "reason": reason, "ts": f"{day}T00:00:00+00:00"}


def trades_of(fills):
    return closed_trades(fills)


def test_rule_of_ignores_venue_notes():
    """Venue notes are appended after '|' and must not change the rule."""
    assert rule_of("trend break: below fast SMA and underwater") == "trend break"
    assert rule_of("trend break: below SMA | alpaca-paper filled @ 315.5") == "trend break"
    assert rule_of("trailing stop hit (26.58 <= 27.29)") == "trailing stop"
    assert rule_of("score turned negative") == "score turned negative"
    assert rule_of("rotation into AAPL") == "rotation"
    assert rule_of("something new") == "other"
    assert rule_of("") == "other"


def test_rule_of_does_not_match_venue_note_as_a_rule():
    """A venue note mentioning a rule name must not win over the real head."""
    assert rule_of("trailing stop hit | note mentions trend break") == "trailing stop"


def test_wilson_handles_the_zero_for_n_case():
    """The 0-for-54 case is the whole reason this exists."""
    lo, hi = wilson(0, 54)
    assert lo == 0.0
    assert 0.0 < hi < 0.10, hi          # a real upper bound, not 0
    assert wilson(0, 0) == (0.0, 0.0)   # no trades, no claim
    lo, hi = wilson(5, 10)
    assert lo < 0.5 < hi


def test_mean_ci_needs_two_points():
    assert all(math.isnan(v) for v in mean_ci([]))
    assert all(math.isnan(v) for v in mean_ci([1.0]))
    lo, hi = mean_ci([1.0, 1.0, 1.0, 1.0])
    assert lo == hi == 1.0              # zero variance


def test_closed_trades_fifo_matches_and_charges_both_legs():
    fills = [buy("X", 10, 100.0, fee=1.0), buy("X", 10, 110.0, fee=1.0),
             sell("X", 10, 120.0, "trailing stop hit", fee=2.0)]
    trades = closed_trades(fills)
    assert len(trades) == 1
    t = trades[0]
    # FIFO takes the 100.0 lot: 1200 - 1000 - (1.0 entry + 2.0 exit) = 197.0
    assert t.symbol == "X"
    assert t.pnl == 197.0
    assert "trailing stop" in t.reason


def test_an_unmatched_sell_is_dropped_not_booked_as_profit():
    """A sell with no matching buy has no known cost, so it is not a data point.

    This module originally booked its full proceeds as profit. Combined with
    scoping by fills, that turned a 1,079 CSL.AX exit into +1,077 of imaginary
    gain. Dropping it is the only honest answer.
    """
    trades = closed_trades([sell("X", 5, 10.0, "trailing stop hit")])
    assert trades == []
    assert uncosted() == ["X"]


def test_scoping_keeps_the_cost_basis_of_an_older_entry():
    """The real bug: scope by exit date, never by filtering fills.

    A position bought in October and sold in November must keep its October
    cost. Filtering fills to November first strips the buy and the exit looks
    like pure profit.
    """
    fills = [buy("CSL", 8.0, 126.0, day="2026-10-07"),
             sell("CSL", 8.0, 133.7, "trailing stop hit", day="2026-11-17")]
    scoped = since(closed_trades(fills), "2026-11-17")
    assert len(scoped) == 1
    assert scoped[0].pnl == pytest.approx(61.6)      # not 1069.6
    assert scoped[0].pnl < 100, "proceeds must not be booked as profit"
    assert uncosted() == []


def test_since_filters_on_exit_day():
    fills = [buy("A", 1, 10.0, day="2026-01-01"),
             sell("A", 1, 11.0, "trailing stop hit", day="2026-01-05"),
             buy("B", 1, 10.0, day="2026-01-01"),
             sell("B", 1, 12.0, "trailing stop hit", day="2026-02-10")]
    all_trades = closed_trades(fills)
    assert len(all_trades) == 2
    assert len(since(all_trades, "2026-02-01")) == 1
    assert since(all_trades, None) == all_trades


def test_a_rule_that_never_wins_is_flagged():
    """Regression for the real defect: 54 exits, zero winners, unnoticed."""
    fills = []
    for i in range(54):
        fills += [buy(f"S{i}", 1, 100.0),
                  sell(f"S{i}", 1, 85.0, "trend break: below fast SMA")]
    rec = by_rule(closed_trades(fills))["trend break"]
    assert rec.n == 54
    assert rec.wins == 0
    assert rec.pnl < 0
    assert rec.verdict().startswith("LOSING MONEY")
    assert "ACT ON THIS" in report(closed_trades(fills))
    assert "Turn it off or fix it" in report(closed_trades(fills))


def test_a_small_sample_is_not_condemned():
    """Nine losing trades is not evidence; it must say so."""
    fills = []
    for i in range(9):
        fills += [buy(f"S{i}", 1, 100.0), sell(f"S{i}", 1, 95.0, "time stop")]
    rec = by_rule(closed_trades(fills))["time stop"]
    assert rec.n == 9
    assert "too few trades" in rec.verdict()
    assert "ACT ON THIS" not in report(closed_trades(fills))


def test_a_mixed_rule_is_not_distinguishable_from_zero():
    """Wins and losses that cancel must not be called either way."""
    rec = RuleRecord("trailing stop", pnl=0.0,
                     trades=[10.0, -10.0] * 15)
    assert rec.n == 30
    assert rec.verdict() == "not distinguishable from zero"


def test_a_winning_rule_is_recognised():
    rec = RuleRecord("trailing stop", pnl=300.0, trades=[10.0] * 30)
    assert rec.verdict().startswith("making money")


def test_divergences_counts_unexecuted_exits():
    fills = [
        sell("A", 1, 10.0, "trend break | alpaca-paper filled @ 10.0"),
        sell("B", 1, 10.0, "trend break | alpaca-paper skipped: not held at alpaca; ledger-only exit"),
        sell("C", 1, 10.0, "trend break | alpaca-paper error: 403 wash trade detected"),
        sell("D", 1, 10.0, "trend break | alpaca-paper-crypto skipped: X not listed at alpaca"),
        buy("E", 1, 10.0),
    ]
    assert divergences(fills) == 3
    assert "bookkeeping, not broker-confirmed fact" in report(
        closed_trades(fills), None, fills)


def test_report_is_honest_with_no_trades():
    assert "No closed trades to attribute" in report([])


def test_report_includes_the_window_caveat_with_equity():
    fills = [buy("X", 1, 100.0), sell("X", 1, 90.0, "trailing stop hit")]
    out = report(closed_trades(fills), [{"ts": "2026-09-06T00:00:00+00:00", "equity": 900.0, "peak": 1000.0},
                         {"ts": "2026-11-17T00:00:00+00:00", "equity": 900.0, "peak": 1000.0}])
    assert "drawdown -10.0%" in out
    assert "Ten weeks is noise" in out
