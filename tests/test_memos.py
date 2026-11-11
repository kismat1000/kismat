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


def test_flat_memo_abstains_instead_of_scoring_zero(tmp_path):
    """A flat memo must not drag the systematic score.

    Regression test for the defect that cost the paper book real entries: the
    engine blended score()==0.0 for a flat memo, and because combined_score()
    weights research at RESEARCH_WEIGHT, "no opinion" acted as a 40% haircut.
    """
    today = date.today()
    write_memo(memo("XLE", "flat", 0.7, today), tmp_path)
    m = load_memos(tmp_path, today=today)["XLE"]
    assert m.abstains
    assert m.research_score(today) is None, "flat must abstain, not score 0.0"
    assert m.score(today) == pytest.approx(0.0)      # reporting value unchanged


def test_directional_memos_still_blend(tmp_path):
    today = date.today()
    write_memo(memo("BTCUSDT", "long", 0.8, today), tmp_path)
    write_memo(memo("ETHUSDT", "avoid", 0.9, today), tmp_path)
    memos = load_memos(tmp_path, today=today)
    assert memos["BTCUSDT"].research_score(today) == pytest.approx(0.8)
    assert memos["ETHUSDT"].research_score(today) == pytest.approx(-0.9)
    assert not memos["BTCUSDT"].abstains


def test_expired_memo_abstains(tmp_path):
    today = date.today()
    write_memo(memo("BTCUSDT", "long", 0.9, today), tmp_path)
    m = load_memos(tmp_path, today=today)["BTCUSDT"]
    assert m.research_score(today + timedelta(days=99)) is None
    assert m.score(today + timedelta(days=99)) == pytest.approx(0.0)


def test_flat_memo_leaves_systematic_score_alone():
    """The whole point: a flat memo must not move the combined score."""
    from kismat.engine import combined_score
    assert combined_score(0.58, None) == pytest.approx(0.58)
    # what the bug did: 0.58 -> 0.348, under the 0.35 entry threshold
    assert combined_score(0.58, 0.0) < 0.35


def test_validate_checks_asset_class():
    assert validate(memo()) == []
    for cls in ("crypto", "us_stocks", "us_etfs", "au_stocks"):
        assert validate({**memo(), "asset_class": cls}) == []
    errs = validate({**memo(), "asset_class": "us_etf"})
    assert any("asset_class" in e for e in errs), errs


def test_schema_enum_matches_validator():
    """The schema the agents write against and the validator must agree."""
    import json
    from pathlib import Path
    from kismat.research.memos import ASSET_CLASSES
    schema = json.loads(Path("prompts/memo_schema.json").read_text())
    assert tuple(schema["properties"]["asset_class"]["enum"]) == ASSET_CLASSES
