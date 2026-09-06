"""Static dashboard: docs/index.html rebuilt after every cycle.

Zero dependencies, zero hosting cost: enable GitHub Pages on the docs/ folder
and it is live. Everything on it comes from the journal and the paper broker.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from kismat.config import DOCS_DIR

STYLE = """
:root{--bg:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--line:#e6e5e1;--series:#2a78d6;
--good:#0ca30c;--critical:#d03b3b;--warning:#fab219}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1a1a19;--panel:#232322;--ink:#fff;
--ink2:#c3c2b7;--line:#383835;--series:#3987e5}}
:root[data-theme="dark"]{--bg:#1a1a19;--panel:#232322;--ink:#fff;--ink2:#c3c2b7;--line:#383835;--series:#3987e5}
body{background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:24px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:24px 0 8px;color:var(--ink2);font-weight:600}
.sub{color:var(--ink2);margin-bottom:16px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.tile .k{color:var(--ink2);font-size:12px}.tile .v{font-size:22px;font-weight:600;margin-top:2px}
.tile .v.pos{color:var(--good)}.tile .v.neg{color:var(--critical)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;color:var(--ink2);font-weight:600;border-bottom:1px solid var(--line);padding:6px 8px}
td{padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}td.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--line)}
.badge.halt{border-color:var(--critical);color:var(--critical)}.badge.ok{border-color:var(--good);color:var(--good)}
svg text{fill:var(--ink2);font-size:11px}.grid{stroke:var(--line);stroke-width:1}.series{stroke:var(--series);stroke-width:2;fill:none}
.muted{color:var(--ink2)}
"""


def _score(d, key):
    v = d.get(key)
    return f"{v:+.2f}" if isinstance(v, (int, float)) else "-"


def _fmt(x, digits=2):
    try:
        return f"{float(x):,.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def equity_svg(points: list[tuple[str, float]], width: int = 900, height: int = 220) -> str:
    if len(points) < 2:
        return '<p class="muted">Equity curve appears after two cycles.</p>'
    pad_l, pad_r, pad_t, pad_b = 56, 12, 12, 28
    ys = [p[1] for p in points]
    lo, hi = min(ys), max(ys)
    if hi - lo < 1e-9:
        lo, hi = lo * 0.99, hi * 1.01
    n = len(points)
    def sx(i): return pad_l + (width - pad_l - pad_r) * i / (n - 1)
    def sy(v): return pad_t + (height - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))
    path = " ".join(f"{'M' if i == 0 else 'L'}{sx(i):.1f},{sy(v):.1f}" for i, (_, v) in enumerate(points))
    grid = []
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        y = sy(v)
        grid.append(f'<line class="grid" x1="{pad_l}" x2="{width - pad_r}" y1="{y:.1f}" y2="{y:.1f}"/>'
                    f'<text x="{pad_l - 6}" y="{y + 4:.1f}" text-anchor="end">{v:,.0f}</text>')
    labels = (f'<text x="{pad_l}" y="{height - 8}">{html.escape(points[0][0][:10])}</text>'
              f'<text x="{width - pad_r}" y="{height - 8}" text-anchor="end">{html.escape(points[-1][0][:10])}</text>')
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Equity curve">'
            + "".join(grid) + f'<path class="series" d="{path}"/>' + labels + "</svg>")


def build(journal, broker, memos: dict, signals: dict, settings, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or DOCS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    eq = journal.read("equity")
    fills = journal.read("fills", limit=25)
    decisions = journal.read("decisions", limit=40)
    events = journal.read("events", limit=15)
    start = settings.risk.starting_cash
    last_eq = eq[-1]["equity"] if eq else start
    ret = last_eq / start - 1 if start else 0.0
    dd = eq[-1].get("drawdown", 0.0) if eq else 0.0
    halted = broker.meta.get("halted", False)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def tile(k, v, cls=""):
        return f'<div class="tile"><div class="k">{k}</div><div class="v {cls}">{v}</div></div>'

    tiles = "".join([
        tile("Equity", _fmt(last_eq)),
        tile("Return since start", f"{ret:+.2%}", "pos" if ret >= 0 else "neg"),
        tile("Drawdown from peak", f"{dd:.2%}", "neg" if dd < -0.03 else ""),
        tile("Cash", _fmt(broker.cash())),
        tile("Open positions", str(len(broker.positions()))),
        tile("Mode", html.escape(settings.mode.upper()) + (" · approval" if settings.approval_mode else "")),
    ])
    status = ('<span class="badge halt">HALTED: ' + html.escape(broker.meta.get("halt_reason", "")) + "</span>"
              if halted else '<span class="badge ok">risk engine active</span>')

    pos_rows = "".join(
        f"<tr><td>{html.escape(s)}</td><td>{html.escape(p['asset_class'])}</td><td class='num'>{p['qty']:.6g}</td>"
        f"<td class='num'>{p['avg_price']:.6g}</td><td class='num'>{p.get('last_price', p['avg_price']):.6g}</td>"
        f"<td class='num'>{(p.get('last_price', p['avg_price']) / p['avg_price'] - 1):+.2%}</td>"
        f"<td class='num'>{(p.get('stop_price') or 0):.6g}</td></tr>"
        for s, p in sorted(broker.positions().items())) or "<tr><td colspan='7' class='muted'>No open positions</td></tr>"

    fill_rows = "".join(
        f"<tr><td>{html.escape(f['ts'][:16])}</td><td>{html.escape(f['symbol'])}</td><td>{f['side']}</td>"
        f"<td class='num'>{f['qty']:.6g}</td><td class='num'>{f['price']:.6g}</td><td>{html.escape(str(f.get('reason', '')))}</td></tr>"
        for f in reversed(fills)) or "<tr><td colspan='6' class='muted'>No fills yet</td></tr>"

    dec_rows = "".join(
        f"<tr><td>{html.escape(d['ts'][:16])}</td><td>{html.escape(d['symbol'])}</td><td class='num'>{_score(d, 'systematic')}</td>"
        f"<td class='num'>{_score(d, 'research')}</td><td class='num'>{_score(d, 'combined')}</td>"
        f"<td>{html.escape(d.get('action', ''))}</td><td>{html.escape(str(d.get('reason', '')))[:120]}</td></tr>"
        for d in [x for x in reversed(decisions) if x.get("action") not in (None, "hold")][:20]) or "<tr><td colspan='7' class='muted'>No buy, sell, skip, or proposal decisions yet</td></tr>"

    memo_rows = "".join(
        f"<tr><td>{html.escape(s)}</td><td>{html.escape(m.data['direction'])}</td><td class='num'>{m.conviction:.2f}</td>"
        f"<td>{html.escape(m.data['date'])}</td><td>{html.escape(m.data['thesis'])[:160]}</td></tr>"
        for s, m in sorted(memos.items())) or "<tr><td colspan='5' class='muted'>No research memos in the last few days</td></tr>"

    sig_rows = "".join(
        f"<tr><td>{html.escape(s)}</td><td class='num'>{v['score']:+.2f}</td><td>{html.escape('; '.join(v.get('reasons', []))[:140])}</td></tr>"
        for s, v in sorted(signals.items(), key=lambda kv: -kv[1]["score"])[:15])

    ev_rows = "".join(f"<li><span class='muted'>{html.escape(e['ts'][:16])}</span> {html.escape(e['kind'])}: {html.escape(e['message'])}</li>"
                      for e in reversed(events)) or "<li class='muted'>No events</li>"

    body = f"""
<h1>Kismat Trading Lab {status}</h1>
<div class="sub">Updated {now}. Paper account in {html.escape(settings.risk.base_currency)}. Every number here comes from state/journal.</div>
<div class="tiles">{tiles}</div>
<h2>Equity</h2><div class="panel">{equity_svg([(e['ts'], e['equity']) for e in eq])}</div>
<h2>Open positions</h2><div class="panel"><table><tr><th>Symbol</th><th>Class</th><th>Qty</th><th>Avg</th><th>Last</th><th>P&amp;L</th><th>Stop</th></tr>{pos_rows}</table></div>
<h2>Latest decisions</h2><div class="panel"><table><tr><th>Time</th><th>Symbol</th><th>Systematic</th><th>Research</th><th>Combined</th><th>Action</th><th>Why</th></tr>{dec_rows}</table></div>
<h2>Recent fills</h2><div class="panel"><table><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Reason</th></tr>{fill_rows}</table></div>
<h2>Research memos in force</h2><div class="panel"><table><tr><th>Symbol</th><th>View</th><th>Conviction</th><th>Date</th><th>Thesis</th></tr>{memo_rows}</table></div>
<h2>Top systematic signals</h2><div class="panel"><table><tr><th>Symbol</th><th>Score</th><th>Reasons</th></tr>{sig_rows}</table></div>
<h2>Events</h2><div class="panel"><ul>{ev_rows}</ul></div>
"""
    path = out_dir / "index.html"
    path.write_text("<!doctype html><html><head><meta charset='utf-8'>"
                    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                    "<title>Kismat Trading Lab</title><style>" + STYLE + "</style></head><body>"
                    + body + "</body></html>")
    (out_dir / "status.json").write_text(json.dumps({"updated": now, "equity": last_eq, "return": ret,
                                                     "drawdown": dd, "halted": halted,
                                                     "positions": len(broker.positions())}, indent=2))
    return path
