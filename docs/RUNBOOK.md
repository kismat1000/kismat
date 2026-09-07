# Runbook: operating Kismat for free

## 1. One-time setup on GitHub

1. Make `main` the default branch: Settings -> General -> Default branch.
   Scheduled workflows only run from the default branch.
2. **Actions**: Settings -> Actions -> General -> allow workflows, and under
   "Workflow permissions" choose "Read and write". The cycle commits state.
3. **Pages**: Settings -> Pages -> Source "Deploy from a branch", branch =
   default branch, folder = `/docs`. The dashboard is then live at
   `https://<user>.github.io/<repo>/`.
4. **Secrets** (Settings -> Secrets and variables -> Actions):
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` for alerts (see step 2).
   - `ANTHROPIC_API_KEY` only if you later want `python -m kismat council`.
5. **Variables**: `KISMAT_APPROVAL_MODE` = `1` for approval mode (phase 1).
6. Run the `trading-cycle` workflow once by hand (Actions -> trading-cycle ->
   Run workflow) and check that a commit "chore(cycle): ..." appears.

Actions minutes: the schedule asks for a cycle every 10 minutes because
GitHub drops many scheduled slots under load; in practice it lands a run every
10 to 60 minutes. Each run takes about a minute. A public repo has no minutes
limit. A private repo gets 2000 free minutes a month, so on a private repo
change the cron in `.github/workflows/cycle.yml` to hourly (`11 * * * *`).
For an exact 30-minute cadence regardless of GitHub's load, point a free
external timer (cron-job.org) at the workflow_dispatch API with a fine-grained
personal access token limited to this repository with Actions read/write.

## 2. Telegram alerts (free, five minutes)

1. In Telegram, message `@BotFather`, send `/newbot`, copy the token.
2. Start a chat with your new bot and send it any message.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id`.
4. Save both as the GitHub secrets above.

You get a message whenever there is a fill, a proposal, or a halt.

## 3. The research council on your Claude plan (no API cost)

The cycle writes `research/packets/<date>.md`. A Claude Code routine turns it
into memos. One is already set up: "Kismat daily research council", daily at
22:30 UTC (08:30 Sydney, after the US close and before the ASX open). Manage
it from the Routines page in Claude Code on the web. If you ever recreate it,
start a fresh session daily with this prompt:

> Check out main in kismat1000/kismat, then follow prompts/routine_research.md exactly.

The routine commits memos to `research/memos/<date>/` and pushes to main. The
next cycle picks them up automatically. Memos older than five days are ignored.

Once a week, on Sunday, the same routine also writes the weekly review. Once a
month, run a session with the prompt "Follow prompts/tooling_scout.md" if you
want upgrade proposals.

## 4. Daily operation

- **Dashboard**: the Pages URL, or `docs/index.html` after a local cycle.
- **Approval mode**: proposals arrive on Telegram with an id. Approve or
  reject from any machine with the repo:

  ```bash
  python -m kismat pending
  python -m kismat approve <id>      # or: approve all
  python -m kismat reject <id>
  git add state && git commit -m "approve" && git push
  ```

- **Journal**: `state/journal/*.jsonl`. `grep` works. Every line has a reason.
- **Kill switch**: after a drawdown of `max_drawdown_pct` from peak (20% for the
  paper test, 5-10% for live) the account liquidates and halts. Nothing trades
  until you run `python -m kismat reset-halt` and push.
  Before you do, read the weekly review and decide what changes.

## 5. Changing limits or the watchlist

Edit `config/risk.yaml` or `config/universe.yaml`, commit, push. The next
cycle uses the new values. Strategy code changes go through a pull request
with `python -m pytest` green and a backtest with an out-of-sample split in
the description.

## 6. Running on your own computer instead

Anything with Python 3.11 works, including a laptop or a Raspberry Pi:

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
python -m kismat cycle          # put this in cron every hour
```

Commit `state/` and `docs/` if you want the dashboard on Pages. n8n is not
needed: it would add a server to host and gives nothing the workflow files do
not already do.

## 7. Broker demo environments (mirrored execution)

With `KISMAT_VENUES=us_stocks=alpaca,crypto=alpaca` (the workflow default)
every US stock and crypto order is also sent to your Alpaca paper account,
which trades the major coins 24/7. Coins Alpaca does not list (BNB, ADA)
stay ledger-only and are journaled as such. `crypto=binance` routes crypto to
Binance Spot Testnet instead, but Binance answers HTTP 451 from GitHub's US
runners, so use it only when the cycle runs from a machine outside the US. The 1,000 USD ledger, the risk engine
and the journal are unchanged; the venues confirm how the order filled and
you can see it in their apps. A venue that is closed, rejects, or is down
never blocks the cycle in paper mode: the ledger still books the trade and
the venue's answer is written to `state/journal/events.jsonl` as a `venue`
event. In live mode the opposite holds: no venue fill, no ledger fill.

Secrets: `ALPACA_KEY`, `ALPACA_SECRET` (paper keys start with `PK`),
`BINANCE_TESTNET_KEY`, `BINANCE_TESTNET_SECRET`. Set the repository variable
`KISMAT_VENUES` to an empty string to go back to the built-in paper broker.

Checks: Actions -> venue-check -> Run workflow pings both venues. Tick "sync"
to place venue orders for ledger positions the venues do not hold yet (a
one-off after switching venues on). Locally: `python -m kismat venue-check`.

Alpaca's paper account starts with 100,000 USD; reset it to 1,000 in the
Alpaca dashboard if you want its numbers to match the ledger. Binance testnet
balances are fixed fake coins and cannot be changed.

## 8. Going live (not before the phase gates in docs/PLAN.md)

1. Open the broker account (Interactive Brokers covers US and ASX with a paper
   account and an API; Binance spot for crypto with its testnet first).
2. Write the adapter against `kismat/execution/broker.py`, test it on the
   broker's paper environment, and add it to the engine behind `KISMAT_MODE`.
3. Start with AUD 100 in approval mode. Set `KISMAT_MODE=live` and
   `KISMAT_LIVE_CONFIRM=I_UNDERSTAND_THE_RISKS` only on the runner you trust.
4. Keep the kill switch. Tighten it for live (5% is reasonable at first).
