from kismat.research.sentiment import score_headlines, tone_by_symbol


def test_tone_counts_words_and_flags_hard_negatives():
    t = score_headlines("ACME", ["ACME beats estimates, shares surge to record",
                                 "ACME faces SEC charges over accounting irregularities"])
    assert t.positive >= 3 and t.score > 0 and t.vetoed and "SEC charges" in t.flags[0]
    calm = score_headlines("ACME", ["ACME to report results next week"])
    assert calm.score == 0 and not calm.vetoed


def test_tone_by_symbol_uses_only_symbol_queries():
    heads = [{"title": "bitcoin rallies to all-time high", "query": "bitcoin"},
             {"title": "markets fall on rate fears", "query": ""},
             {"title": "ethereum exploit drains bridge", "query": "ethereum"}]
    tones = tone_by_symbol(heads, {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "SOLUSDT": "solana"})
    assert tones["BTCUSDT"].score > 0 and not tones["BTCUSDT"].vetoed
    assert tones["ETHUSDT"].vetoed
    assert tones["SOLUSDT"].headlines == 0 and tones["SOLUSDT"].score == 0
