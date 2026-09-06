"""Optional: run the research council through the Claude API.

This only runs when ANTHROPIC_API_KEY is set. Without a key the packet is
built and a Claude Code Routine does the research on your existing plan.

Council: bull analyst -> bear analyst -> judge. The judge sees both sides
and returns a memo that matches prompts/memo_schema.json exactly (enforced by
structured outputs).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import ROOT
from kismat.research.memos import write_memo

log = logging.getLogger(__name__)
PROMPTS = ROOT / "prompts"
MODEL = "claude-opus-5"
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 6}


def _prompt(name: str) -> str:
    return (PROMPTS / name).read_text()


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def _call(client, system: str, user: str, *, effort: str = "medium", tools=None, schema=None):
    kwargs = dict(model=MODEL, max_tokens=16000, system=system,
                  messages=[{"role": "user", "content": user}],
                  output_config={"effort": effort, **({"format": {"type": "json_schema", "schema": schema}} if schema else {})},
                  betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    if tools:
        kwargs["tools"] = tools
    response = client.beta.messages.create(**kwargs)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {getattr(response, 'stop_details', None)}")
    return response


def research_symbol(client, symbol: str, asset_class: str, packet_excerpt: str,
                    root: Path | None = None) -> Path:
    desk = _prompt("00_desk_rules.md")
    context = f"Symbol: {symbol}\nAsset class: {asset_class}\n\nContext from today's packet:\n{packet_excerpt}"

    bull = _text(_call(client, desk + "\n\n" + _prompt("bull_analyst.md"), context, tools=[WEB_SEARCH]))
    bear = _text(_call(client, desk + "\n\n" + _prompt("bear_analyst.md"), context, tools=[WEB_SEARCH]))

    schema = json.loads((PROMPTS / "memo_schema.json").read_text())
    schema.pop("$schema", None)
    schema.pop("title", None)
    judge_input = (f"{context}\n\n## Bull analyst\n{bull}\n\n## Bear analyst\n{bear}\n\n"
                   f"Today is {datetime.now(timezone.utc).date().isoformat()}. Write the memo.")
    judged = _call(client, desk + "\n\n" + _prompt("judge.md"), judge_input, effort="high", schema=schema)
    memo = json.loads(_text(judged))
    memo["agent"] = "council/judge(api)"
    memo["date"] = datetime.now(timezone.utc).date().isoformat()
    memo["symbol"], memo["asset_class"] = symbol, asset_class
    return write_memo(memo, root)


def run_council(symbols: list[tuple[str, str]], packet_path: Path, root: Path | None = None) -> list[Path]:
    import anthropic  # optional dependency
    client = anthropic.Anthropic()
    packet = packet_path.read_text()
    written = []
    for symbol, asset_class in symbols:
        try:
            written.append(research_symbol(client, symbol, asset_class, packet[:12000], root))
            log.info("memo written for %s", symbol)
        except Exception as exc:
            log.error("council failed for %s: %s", symbol, exc)
    return written
