from __future__ import annotations

from seo_engine.keywords import discover_keywords, find_keyword_gaps
from seo_engine.models import Page


def _pages(texts: list[str]) -> list[Page]:
    return [Page(url=f"https://ex.com/{i}", text=txt) for i, txt in enumerate(texts)]


def test_discover_keywords_ranks_theme():
    pages = _pages(
        [
            "running shoes for marathon training and long distance running",
            "trail running shoes with grip for muddy running trails",
        ]
    )
    kws = discover_keywords(pages, max_n=2, top_k=10)
    terms = {k.keyword for k in kws}
    assert "running" in terms
    # results are sorted by score descending
    scores = [k.score for k in kws]
    assert scores == sorted(scores, reverse=True)


def test_discover_keywords_empty():
    assert discover_keywords([]) == []


def test_keyword_gap_finds_missing_terms():
    competitors = _pages(
        [
            "waterproof hiking boots with ankle support for mountain trekking",
            "insulated hiking boots for winter mountain expeditions",
        ]
    )
    own = _pages(["basic sneakers for city walking and casual wear"])
    gaps = find_keyword_gaps(competitor_pages=competitors, own_pages=own, top_k=20)
    gap_terms = {g.keyword for g in gaps}
    # competitor emphasizes hiking/boots/mountain; we don't -> should be gaps
    assert any("hiking" in term or "boots" in term or "mountain" in term for term in gap_terms)
    # all reported as missing (own corpus never mentions them)
    for g in gaps:
        if g.keyword in {"hiking", "boots", "mountain"}:
            assert g.status == "missing"
            assert g.own_score == 0.0
    # sorted by gap descending
    gvals = [g.gap for g in gaps]
    assert gvals == sorted(gvals, reverse=True)


def test_keyword_gap_no_competitors():
    assert find_keyword_gaps(competitor_pages=[], own_pages=_pages(["x"])) == []


def test_keyword_gap_no_own_pages_all_missing():
    competitors = _pages(["quantum computing qubits entanglement"])
    gaps = find_keyword_gaps(competitor_pages=competitors, own_pages=[])
    assert gaps
    assert all(g.status == "missing" for g in gaps)
