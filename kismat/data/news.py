"""Free headlines from RSS. No keys, no cost.

Headlines feed the research packet that the research agents read. The Python
side never tries to "understand" news; that is the agents' job.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import quote_plus

log = logging.getLogger(__name__)

GENERAL_FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "cnbc_markets": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "abc_au_business": "https://www.abc.net.au/news/feed/51892/rss.xml",
    "fed_press": "https://www.federalreserve.gov/feeds/press_all.xml",
}


def google_news_feed(query: str, region: str = "AU") -> str:
    lang = "en-AU" if region == "AU" else "en-US"
    ceid = f"{region}:en"
    return (f"https://news.google.com/rss/search?q={quote_plus(query)}"
            f"&hl={lang}&gl={region}&ceid={ceid}")


@dataclass
class Headline:
    source: str
    title: str
    link: str
    published: str
    query: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_feed(name: str, url: str, limit: int = 15, query: str = "") -> list[Headline]:
    try:
        import feedparser
        parsed = feedparser.parse(url)
    except Exception as exc:
        log.warning("feed %s failed: %s", name, exc)
        return []
    out: list[Headline] = []
    for entry in parsed.entries[:limit]:
        published = entry.get("published", "") or entry.get("updated", "")
        out.append(Headline(source=name, title=entry.get("title", "").strip(),
                            link=entry.get("link", ""), published=published, query=query))
    return out


def fetch_headlines(symbol_queries: dict[str, str] | None = None,
                    per_feed: int = 12) -> list[Headline]:
    """General market feeds plus one Google News search per symbol query."""
    items: list[Headline] = []
    for name, url in GENERAL_FEEDS.items():
        items.extend(fetch_feed(name, url, limit=per_feed))
    for symbol, query in (symbol_queries or {}).items():
        items.extend(fetch_feed(f"gnews:{symbol}", google_news_feed(query),
                                limit=6, query=query))
    seen = set()
    unique: list[Headline] = []
    for h in items:
        key = h.title.lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(h)
    return unique


def default_query_for(symbol: str, asset_class: str) -> str:
    if asset_class == "crypto":
        base = symbol.replace("USDT", "").replace("USD", "")
        names = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "bnb binance coin",
                 "XRP": "xrp ripple", "ADA": "cardano", "AVAX": "avalanche crypto",
                 "LINK": "chainlink", "DOGE": "dogecoin", "LTC": "litecoin"}
        return names.get(base, f"{base} crypto")
    if asset_class == "au_stocks":
        return f"{symbol.replace('.AX', '')} ASX shares"
    if asset_class == "us_etfs":
        return f"{symbol} ETF"
    return f"{symbol} stock"


def snapshot(headlines: list[Headline]) -> dict:
    return {"fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(headlines), "items": [h.to_dict() for h in headlines]}
