# Claude Code routine: daily research council

You are running inside the kismat repository on a schedule. Do the following
end to end, then stop.

1. `git pull` the default branch. Read prompts/00_desk_rules.md.
2. Open the newest file in research/packets/. If none exists, run
   `python -m kismat cycle --quiet` first (needs `pip install -r requirements.txt`).
3. Run prompts/scanner.md against the packet: at most eight symbols a day.
   Holdings (state/paper/portfolio.json) without a memo from the last three
   days come first, then up to three new candidates. Holdings with a fresh
   memo are skipped unless something material changed.
4. For each pick run the council: prompts/bull_analyst.md, then
   prompts/bear_analyst.md, then prompts/macro_analyst.md once for the day,
   then prompts/judge.md. Use web search for every analyst step. Cite dated
   sources.
5. Write each judge memo to research/memos/<today>/<SYMBOL>.json following
   prompts/memo_schema.json. Run `python -m kismat validate-memos` and fix any
   invalid memo.
6. Commit only files under research/ with the message
   "research: council memos <today>" and push to the default branch.
7. If it is Sunday, also run `python -m kismat review` and then
   prompts/weekly_review.md, and commit the review.
8. If a memo says "avoid" with conviction 0.7 or more on a held position, say
   so in one line at the end of your final message so the alert is visible.

Never edit config/, kismat/, or tests/ in this routine. Improvements go
through prompts/quant_analyst.md proposals and a separate pull request.
