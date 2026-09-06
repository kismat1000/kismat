from datetime import date, timedelta

import pytest

from kismat.research.memos import load_memos, validate, write_memo


def memo(symbol="BTCUSDT", direction="long", conviction=0.8, d=None):
    return {"symbol": symbol, "asset_class": "crypto", "date": (d or date.today()).isoformat(),
            "direction": direction, "conviction": conviction, "thesis": "t", "bull_case": "b",
            "bear_case": "r", "catalysts": ["c"], "risks": ["x"], "invalidation": "i",
            "horizon_days": 10, "sources": ["https://example.com"], "agent": "test"}


def test_validate_catches_bad_memos():
    assert validate(memo()) == []
    bad = memo(direction="short")
    assert validate(bad)
    assert validate({"symbol": "X"})
    assert validate(memo(conviction=1.5))


def test_load_latest_score_decay_and_veto(tmp_path):
    today = date.today()
    write_memo(memo(d=today - timedelta(days=2), conviction=0.5), tmp_path)
    write_memo(memo(d=today, conviction=0.8), tmp_path)
    write_memo(memo("ETHUSDT", "avoid", 0.9, today), tmp_path)
    write_memo(memo("OLD", "long", 0.9, today - timedelta(days=30)), tmp_path)
    memos = load_memos(tmp_path, today=today)
    assert set(memos) == {"BTCUSDT", "ETHUSDT"}
    assert memos["BTCUSDT"].conviction == 0.8
    assert memos["BTCUSDT"].score(today) == pytest.approx(0.8)
    assert memos["ETHUSDT"].score(today) == pytest.approx(-0.9)
    assert memos["ETHUSDT"].vetoes_entry(today)
    assert not memos["BTCUSDT"].vetoes_entry(today)
    older = load_memos(tmp_path, today=today + timedelta(days=3))
    assert 0 < older["BTCUSDT"].score(today + timedelta(days=3)) < 0.8


def test_write_memo_rejects_invalid(tmp_path):
    with pytest.raises(ValueError):
        write_memo(memo(direction="nope"), tmp_path)
