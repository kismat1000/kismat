# Tooling scout (monthly)

Look for things that would make this desk better, cheaper, or safer. Use web
search. Candidates: new free data sources, better free market data APIs,
broker APIs that support paper trading, new model releases or API features
for the research council, backtesting libraries, alerting options.

For each finding:
- What it is, what it replaces or adds, cost (must stay free or near free).
- Concrete integration plan touching which files.
- Risk: what could break, and how to test it.

Write to research/proposals/<date>-tooling.md. Any code change becomes a pull
request with passing tests. Nothing self-installs into a live trading loop.
