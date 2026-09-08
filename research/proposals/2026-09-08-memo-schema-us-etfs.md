# Proposal: add `us_etfs` to the memo schema's asset_class enum

- date: 2026-09-08
- author: council/desk
- status: proposed (not implemented; prompts/memo_schema.json unchanged)

## Defect
`config/universe.yaml` defines four asset classes: `us_stocks`, `us_etfs`, `au_stocks` and
crypto. `prompts/memo_schema.json` allows only three:

```json
"asset_class": {"type": "string", "enum": ["crypto", "us_stocks", "au_stocks"]}
```

The engine bought DBC (an `us_etfs` symbol) on 2026-09-08, and XLE, XLF, XLV and other ETFs
are live candidates in today's packet. Any memo written for them is unrepresentable: the
truthful value violates the schema, and a schema-valid value misdescribes the asset.

This has been silently survivable because `kismat/research/memos.py: validate()` checks
required keys, direction, conviction, date, list types and horizon_days — but never
`asset_class` against the enum. So `python -m kismat validate-memos` passes memos the
documented schema rejects. Today's DBC memo is exactly that: it validates, and it is
schema-invalid.

## Proposed change
Add `us_etfs` to the enum in `prompts/memo_schema.json`, so it reads
`["crypto", "us_stocks", "us_etfs", "au_stocks"]`, matching `config/universe.yaml`.

Separately worth considering: have `validate()` check `asset_class` against that enum, so
the validator and the schema stop disagreeing. That is a code change and belongs in its own
pull request, not here.

## Interim behaviour
Today's DBC memo uses `"asset_class": "us_etfs"` — the truthful value, matching the packet's
own label and `config/universe.yaml`. Describing a broad commodity-futures ETF as `us_stocks`
to satisfy a stale enum would put a false fact in the memo to pass a check, which is the
wrong trade.

## Why it might be wrong
If the enum is deliberately narrow because something downstream keys off exactly three
values, widening it could surprise that consumer. I did not find such a consumer, but I did
not audit every reader of `asset_class` either.
