# Kismat

A research-first, risk-first trading lab that runs for free. Paper trading by
default. Real money only after it has earned a track record.

## What it does

Every two hours a cycle runs:

```
free data (Binance, Yahoo, RSS)
   -> systematic signals (trend, momentum, breakout, volatility filter)
   -> research memos from the agent council (bull, bear, macro, judge)
   -> risk engine (1% risk per trade, position caps, daily loss stop, kill switch)
   -> paper broker
   -> journal (every decision, fill, and equity snapshot as JSONL)
   -> Telegram alert + static dashboard
```

Once a day a Claude Code routine reads the research packet the cycle produced,
runs the council prompts in `prompts/` with web search, and commits memos back
into `research/memos/`. The next cycle merges those memos into its decisions.
Once a week a review packet is built from the journal so the desk learns from
its own mistakes.

## Honest expectations

Nothing here predicts prices. The edge, if there is one, comes from discipline:
systematic entries, hard stops, small positions, and research that is checked
against outcomes. On a small account the realistic goal for the first months
is a clean, verified paper record and a system you trust. Read
[docs/PLAN.md](docs/PLAN.md) before expecting anything else.

## Quick start (local)

```bash
pip install -r requirements.txt
python -m pytest -q                       # 23 tests, all offline
python -m kismat backtest --synthetic     # offline sanity check
python -m kismat backtest --asset-class crypto --days 400   # real data
python -m kismat cycle                    # one paper cycle, writes state/ and docs/index.html
python -m kismat status
```

Open `docs/index.html` in a browser for the dashboard.

## Running it for free, all the time

See [docs/RUNBOOK.md](docs/RUNBOOK.md). Short version:

| Piece | Where it runs | Cost |
|---|---|---|
| Trading cycle | GitHub Actions cron (`.github/workflows/cycle.yml`) | free minutes |
| Research council | Claude Code routine on your existing plan (`prompts/routine_research.md`) | included in plan |
| Dashboard | GitHub Pages serving `docs/` | free |
| Alerts | Telegram bot | free |
| Market data | Binance public API, Yahoo Finance, RSS | free |
| State | JSON and JSONL files committed to this repo | free |

## Safety switches

- `KISMAT_MODE` defaults to `paper`. Live needs `KISMAT_MODE=live` **and**
  `KISMAT_LIVE_CONFIRM=I_UNDERSTAND_THE_RISKS`, and no live adapter is wired yet.
- `KISMAT_APPROVAL_MODE=1` turns entries into proposals you approve from the CLI.
- `config/risk.yaml` holds every limit. The risk engine is plain code; no
  prompt or memo can override it.
- The kill switch liquidates and halts at a 10% drawdown from peak. Only a
  human can clear it: `python -m kismat reset-halt`.

## Layout

```
kismat/            the Python package (data, strategy, risk, execution, research, journal, dashboard)
config/            universe.yaml (watchlist) and risk.yaml (limits)
prompts/           the agent council: desk rules, scanner, bull, bear, macro, quant, judge, risk officer, reviews
research/          memos, packets, news snapshots, proposals, reviews (written by the cycle and the agents)
state/             paper portfolio and the JSONL journal (committed by the cycle workflow)
docs/              dashboard (index.html), PLAN.md, RUNBOOK.md
tests/             offline test suite
```
