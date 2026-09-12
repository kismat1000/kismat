from datetime import date

from kismat.data.events import in_blackout


def test_in_blackout_window_is_inclusive_and_forward_only():
    dates = [date(2026, 1, 10), date(2026, 4, 20)]
    assert in_blackout(dates, date(2026, 4, 17), 3) == date(2026, 4, 20)
    assert in_blackout(dates, date(2026, 4, 20), 3) == date(2026, 4, 20)
    assert in_blackout(dates, date(2026, 4, 16), 3) is None
    assert in_blackout(dates, date(2026, 4, 21), 3) is None      # already reported
    assert in_blackout(dates, date(2026, 4, 18), 0) is None      # off
