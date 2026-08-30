"""Competitive keyword discovery + gap analysis (content-based).

Honest scope: this discovers the keywords a set of competitor pages are
*written about* using TF-IDF over their real content, then contrasts that with
your own pages to surface gaps. It does **not** pull ranking/volume data from
Ahrefs/Semrush clickstream indexes — that requires paid APIs. What it gives you
is grounded, explainable, and free: the actual language competitors optimize
for that you under-serve.

If you later wire in a SERP/volume source, ``KeywordGap.gap`` is the natural
field to multiply by search volume.
"""

from __future__ import annotations

from collections import Counter

from . import text as textmod
from .models import KeywordGap, KeywordStat, Page


def _corpus_keyword_scores(
    pages: list[Page], *, max_n: int
) -> tuple[dict[str, float], dict[str, int], dict[str, int]]:
    """Aggregate per-corpus keyword weight, document freq, and raw occurrences."""
    docs = [p.text or "" for p in pages]
    vectors, df = textmod.tfidf_corpus(docs, max_n=max_n)

    # Sum tf-idf weight of each term across documents -> corpus-level salience.
    agg: dict[str, float] = {}
    for vec in vectors:
        for term, weight in vec.items():
            agg[term] = agg.get(term, 0.0) + weight

    occurrences: Counter[str] = Counter()
    for d in docs:
        occurrences.update(textmod.term_frequencies(d, max_n=max_n))

    return agg, df, dict(occurrences)


def discover_keywords(
    pages: list[Page], *, max_n: int = 3, top_k: int = 50, min_documents: int = 1
) -> list[KeywordStat]:
    """Rank the keywords a corpus is most about.

    ``min_documents`` filters one-off noise: require a term to appear on at
    least this many pages before it counts as a corpus theme.
    """
    if not pages:
        return []
    agg, df, occ = _corpus_keyword_scores(pages, max_n=max_n)
    normalized = textmod.normalize_scores(agg)

    stats = [
        KeywordStat(
            keyword=term,
            score=round(normalized[term], 6),
            documents=df.get(term, 0),
            occurrences=occ.get(term, 0),
        )
        for term in normalized
        if df.get(term, 0) >= min_documents
    ]
    # Deterministic ordering: score desc, then keyword asc for ties.
    stats.sort(key=lambda s: (-s.score, s.keyword))
    return stats[:top_k]


def find_keyword_gaps(
    *,
    competitor_pages: list[Page],
    own_pages: list[Page],
    max_n: int = 3,
    top_k: int = 50,
    min_competitor_documents: int = 1,
    underused_ratio: float = 0.5,
) -> list[KeywordGap]:
    """Keywords competitors emphasize that you miss or underuse.

    * ``missing``   — the term never appears in your own corpus.
    * ``underused`` — your salience is below ``underused_ratio`` of theirs.

    Results are sorted by ``gap`` descending: the biggest, most actionable
    opportunities first.
    """
    if not competitor_pages:
        return []

    comp_scores, comp_df, _ = _corpus_keyword_scores(competitor_pages, max_n=max_n)
    comp_norm = textmod.normalize_scores(comp_scores)

    if own_pages:
        own_scores, _, _ = _corpus_keyword_scores(own_pages, max_n=max_n)
        own_norm = textmod.normalize_scores(own_scores)
    else:
        own_norm = {}

    gaps: list[KeywordGap] = []
    for term, comp_score in comp_norm.items():
        if comp_df.get(term, 0) < min_competitor_documents:
            continue
        own_score = own_norm.get(term, 0.0)

        if own_score == 0.0:
            status = "missing"
        elif own_score < comp_score * underused_ratio:
            status = "underused"
        else:
            continue  # you already cover it adequately

        gaps.append(
            KeywordGap(
                keyword=term,
                competitor_score=round(comp_score, 6),
                own_score=round(own_score, 6),
                gap=round(comp_score - own_score, 6),
                competitor_documents=comp_df.get(term, 0),
                status=status,
            )
        )

    gaps.sort(key=lambda g: (-g.gap, g.keyword))
    return gaps[:top_k]
