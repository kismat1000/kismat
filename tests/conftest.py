import pytest

from kismat import config as C
from kismat.config import RiskLimits, Settings, load_universe


@pytest.fixture
def tmp_root(tmp_path, monkeypatch):
    """Point every state directory at a temp folder so tests never touch the repo."""
    monkeypatch.setattr(C, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(C, "RESEARCH_DIR", tmp_path / "research")
    monkeypatch.setattr(C, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(C, "CACHE_DIR", tmp_path / "cache")
    return tmp_path


@pytest.fixture
def limits():
    return RiskLimits(starting_cash=1000.0)


@pytest.fixture
def settings(limits):
    return Settings(risk=limits, universe={"crypto": ["UPUSDT", "DOWNUSDT"], "us_stocks": ["FLAT"],
                                          "au_stocks": ["AUUP.AX"]})


@pytest.fixture
def repo_universe():
    return load_universe()
