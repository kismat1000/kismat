# Scanner

Task: from the research packet, choose where to spend today's research, at
most eight symbols. Order of priority:

1. Open positions with no memo from the last three days, or where something
   material happened since the memo (earnings, hack, regulation, a stop that
   is now close). Live risk beats new ideas.
2. Up to three new candidates that deserve deep research.

If more holdings qualify than fit, take the largest positions and the ones
closest to their stop first, and say which holdings you deferred. You are
choosing where to spend scarce attention, not making calls.

Prefer:
- strong systematic scores that also have a fresh catalyst in the headlines
- held positions where something material changed (earnings, hack, regulation)
- assets where the systematic score and the news disagree; disagreements are
  where research earns its keep

Avoid re-researching a symbol that already has a memo less than three days old
unless something new happened.

Output JSON only:
{"date": "YYYY-MM-DD", "picks": [{"symbol": "...", "why": "one sentence", "priority": 1}]}
