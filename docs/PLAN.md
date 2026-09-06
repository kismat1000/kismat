# Plan

## The decision you asked about: is research the core?

Research is necessary and it is not sufficient. Three things decide whether a
small account survives, in this order:

1. **Risk management.** Position size, stops, and the kill switch decide how
   long you stay in the game. This is where most retail accounts actually die.
2. **Process.** Systematic entries and exits, a journal, and weekly review.
   This is what turns a hunch into a track record you can trust.
3. **Research.** This is where an edge can come from, and it is the part the
   agent council does. It sharpens the systematic signal (a strong "avoid" memo
   vetoes a trade, a strong "long" memo lifts the score) and it finds catalysts
   the price data alone cannot see.

"Know where the market might go" is not achievable. What is achievable is
knowing when the odds are slightly in your favour, betting small, and letting
the winners run. That is the whole design.

## Meme coin launch: declined

Creating a token and selling everything at the top onto the people who bought
it is a pump-and-dump. It is fraud in most jurisdictions, including Australia,
and it hurts real people. This repo will not do it. Trading existing meme
coins with strict rules is possible later; the desk rules mark manipulated or
illiquid assets as "avoid" for a reason.

## Phases and promotion gates

| Phase | What runs | Gate to the next phase |
|---|---|---|
| 0. Build | this repository | tests green, one clean cycle on real data |
| 1. Paper, approval mode | cycle every 2h, council daily, you approve entries | 6 weeks, 30+ closed trades, drawdown under 10%, weekly reviews written |
| 2. Paper, autonomous | same, entries fill automatically | 8 more weeks, positive expectancy after costs, memo calibration checked |
| 3. Live, tiny | AUD 100, real broker adapter, approval mode | 8 weeks live matching paper within slippage |
| 4. Live, scaled | AUD 1000, autonomous within limits | reviewed monthly, limits tightened before they are loosened |

Nothing moves to the next phase because it "feels ready". The numbers in the
gate column decide.

## Markets and brokers

| Market | Data (free) | Paper | Live candidates |
|---|---|---|---|
| Crypto | Binance public API | built-in paper broker | Binance spot API (Binance Australia for AUD), Coinbase Advanced |
| US stocks | Yahoo Finance | built-in paper broker | Interactive Brokers (AU residents welcome, API, paper account), Alpaca if available to you, Moomoo AU OpenAPI |
| ASX | Yahoo Finance | built-in paper broker | Interactive Brokers, Moomoo AU |

Spaceship has no trading API, so it stays a manual account. Phantom is a
wallet, not a broker; on-chain Solana swaps (Jupiter) can be an adapter later,
after the desk has proven itself on liquid assets.

## How "self-training" works here

- **Journal.** Every decision records the systematic score, the research
  score, the risk verdict, and the reason. Every fill and every equity snapshot
  is logged. `python -m kismat review` turns that into a review packet.
- **Weekly review agent** (`prompts/weekly_review.md`) reads the packet,
  names what was wrong, checks memo calibration, and proposes one testable
  change.
- **Quant analyst** (`prompts/quant_analyst.md`) turns proposals into rules
  with a backtest and an out-of-sample split. Only a pull request with passing
  tests changes strategy code.
- **Tooling scout** (`prompts/tooling_scout.md`) looks monthly for better
  free data, broker APIs, and model features, and proposes upgrades as pull
  requests.
- **Memo decay.** A memo's influence fades to zero over five days so stale
  research cannot steer trades.

What it deliberately does not do: continuously refit parameters to the last
few weeks of data. That is the fastest way to overfit noise and blow up.

## Council prompting

Every symbol that reaches the judge has been argued from both sides with
sources, and the judge is told to prefer "flat" over a forced idea. The
scanner limits attention to five symbols a day so each one gets real work.
The risk officer can only veto or shrink. This is the "multiple prompting"
you asked for: independent roles, adversarial by design, structured output
enforced by a schema.

## Roadmap after phase 1

- Broker adapters: Binance spot (testnet first), Interactive Brokers paper.
- Intraday stop checks using live prices between daily bars.
- Council via the Claude API when a budget exists (`python -m kismat council`).
- Portfolio-level correlation caps in the risk engine.
- Rotation (built, off by default): when the book is full, the weakest holding
  is replaced by a candidate that beats it by `rotation_margin`. The first
  two-year backtest favoured no rotation (+18.0% vs +14.1%, better Sharpe and
  drawdown), so it stays off until the weekly backtest says otherwise.
- Trend-break exit (kept): turning it off helped US stocks but hurt crypto
  and ASX, and without rotation it was disastrous (+1.4%), so it stays on.
- Memo calibration report: conviction buckets versus realised outcomes.
