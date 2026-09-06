"""Settings: environment variables plus the YAML files under config/.

Everything defaults to the safest option. Live trading needs two explicit
switches so it can never happen by accident.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("KISMAT_ROOT", Path(__file__).resolve().parent.parent))
CONFIG_DIR = ROOT / "config"
STATE_DIR = ROOT / "state"
RESEARCH_DIR = ROOT / "research"
DOCS_DIR = ROOT / "docs"
CACHE_DIR = ROOT / "data_cache"

ASSET_CLASSES = ("crypto", "us_stocks", "au_stocks")


@dataclass
class RiskLimits:
    starting_cash: float = 1000.0
    base_currency: str = "USD"
    max_position_pct: float = 0.15
    max_positions: int = 6
    max_asset_class_pct: dict = field(
        default_factory=lambda: {"crypto": 0.5, "us_stocks": 0.6, "au_stocks": 0.6}
    )
    per_trade_risk_pct: float = 0.01
    stop_atr_multiple: float = 2.5
    trend_break_exit: bool = True
    min_trade_value: float = 10.0
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.10
    entry_score_threshold: float = 0.35
    exit_score_threshold: float = -0.10
    rotation_margin: float = 0.0
    min_hold_days: int = 1
    fees_bps: dict = field(
        default_factory=lambda: {"crypto": 10, "us_stocks": 5, "au_stocks": 15}
    )
    slippage_bps: float = 5.0

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "RiskLimits":
        path = path or CONFIG_DIR / "risk.yaml"
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text()) or {}
        known = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
        return cls(**known)

    def fee_bps(self, asset_class: str) -> float:
        return float(self.fees_bps.get(asset_class, 10))


@dataclass
class Settings:
    mode: str = "paper"                 # "paper" or "live"
    live_confirm: str = ""              # must equal "I_UNDERSTAND_THE_RISKS" for live
    approval_mode: bool = False         # True: entries become proposals, not fills
    lookback_days: int = 400
    cache_ttl_hours: float = 6.0
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    anthropic_api_key: str = ""
    venues: dict = field(default_factory=dict)      # asset_class -> "alpaca" | "binance"
    alpaca_key: str = ""
    alpaca_secret: str = ""
    binance_key: str = ""
    binance_secret: str = ""
    risk: RiskLimits = field(default_factory=RiskLimits)
    universe: dict = field(default_factory=dict)

    @property
    def is_live(self) -> bool:
        return self.mode == "live" and self.live_confirm == "I_UNDERSTAND_THE_RISKS"

    @classmethod
    def load(cls) -> "Settings":
        env = os.environ
        universe = load_universe()
        return cls(
            mode=env.get("KISMAT_MODE", "paper").lower(),
            live_confirm=env.get("KISMAT_LIVE_CONFIRM", ""),
            approval_mode=env.get("KISMAT_APPROVAL_MODE", "0") in ("1", "true", "yes"),
            lookback_days=int(env.get("KISMAT_LOOKBACK_DAYS", "400")),
            cache_ttl_hours=float(env.get("KISMAT_CACHE_TTL_HOURS", "6")),
            telegram_bot_token=env.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=env.get("TELEGRAM_CHAT_ID", ""),
            anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
            venues=parse_venues(env.get("KISMAT_VENUES", "")),
            alpaca_key=env.get("ALPACA_KEY", ""),
            alpaca_secret=env.get("ALPACA_SECRET", ""),
            binance_key=env.get("BINANCE_TESTNET_KEY", "") or env.get("BINANCE_KEY", ""),
            binance_secret=env.get("BINANCE_TESTNET_SECRET", "") or env.get("BINANCE_SECRET", ""),
            risk=RiskLimits.from_yaml(),
            universe=universe,
        )


def parse_venues(spec: str) -> dict[str, str]:
    """'us_stocks=alpaca,crypto=binance' -> {'us_stocks': 'alpaca', 'crypto': 'binance'}"""
    out: dict[str, str] = {}
    for part in spec.split(","):
        if "=" in part:
            cls, name = part.split("=", 1)
            if cls.strip() in ASSET_CLASSES and name.strip():
                out[cls.strip()] = name.strip().lower()
    return out


def load_universe(path: Path | None = None) -> dict[str, list[str]]:
    path = path or CONFIG_DIR / "universe.yaml"
    if not path.exists():
        return {k: [] for k in ASSET_CLASSES}
    raw = yaml.safe_load(path.read_text()) or {}
    return {k: list(raw.get(k, []) or []) for k in ASSET_CLASSES}


def symbol_classes(universe: dict[str, list[str]]) -> dict[str, str]:
    """Map every symbol to its asset class."""
    out: dict[str, str] = {}
    for cls, symbols in universe.items():
        for s in symbols:
            out[s] = cls
    return out


def ensure_dirs() -> None:
    for d in (STATE_DIR, STATE_DIR / "journal", STATE_DIR / "paper",
              RESEARCH_DIR / "memos", RESEARCH_DIR / "packets", DOCS_DIR, CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
