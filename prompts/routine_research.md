# Claude Code routine: daily research council

You are running inside the kismat repository on a schedule. Do the following
end to end, then stop.

1. `git pull` the default branch. Read prompts/00_desk_rules.md.
2. Learn before you research: read the last 20 lines of research/lessons.md
   (one line per closed trade, with what went wrong or right) and the
   `summary` block of research/outcomes.json (win rate, P&L by exit reason,
   how often memos by direction and conviction were right). Note in one line
   what the record says about the desk's own calls, and let it shape today's
   conviction: if long memos have been wrong lately, say so and be stingier.
3. Open the newest file in research/packets/. If none exists, run
   `python -m kismat cycle --quiet` first (needs `pip install -r requirements.txt`).
   The packet's signal table now carries pattern columns (52w = distance below
   the 252-day high, rs = momentum minus the class benchmark's, squeeze = ATR
   against its median, news = headline tone, "!" = hard-negative headline) and
   a section "Event and news gates in force today" listing symbols the engine
   will not enter today and why.
4. Run prompts/scanner.md against the packet: at most eight symbols a day.
   Holdings (state/paper/portfolio.json) without a memo from the last three
   days come first, then up to three new candidates. Holdings with a fresh
   memo are skipped unless something material changed.
5. For each pick run the council: prompts/pattern_analyst.md (price structure
   from the packet's numbers, no web search needed), then
   prompts/bull_analyst.md, then prompts/bear_analyst.md, then
   prompts/macro_analyst.md once for the day, then prompts/judge.md. Use web
   search for the bull, bear, and macro steps. Cite dated sources. The judge
   must name the pattern analyst's invalidation level in the memo.
6. Write each judge memo to research/memos/<today>/<SYMBOL>.json following
   prompts/memo_schema.json. Run `python -m kismat validate-memos` and fix any
   invalid memo.
7. Append today's entry to research/desk_log.md: symbols, direction and
   conviction per memo, deferred holdings, the lesson or outcome statistic
   that changed a call today (or "none"), and anything that failed.
8. Commit only files under research/ with the message
   "research: council memos <today>" and push to the default branch.
9. If it is Sunday, also run `python -m kismat review` and then
   prompts/weekly_review.md, and commit the review.
10. If a memo says "avoid" with conviction 0.7 or more on a held position, say
    so in one line at the end of your final message so the alert is visible.

Never edit config/, kismat/, or tests/ in this routine. Improvements go
through prompts/quant_analyst.md proposals and a separate pull request.
