"""Pure-Python text utilities: tokenization, n-grams, TF-IDF and cosine.

No numpy, no scikit-learn, no network. This keeps the engine light, fully
deterministic, and trivially testable — the same input always yields the same
scores, which matters for a system that must not surprise its operator.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

# A compact, dependency-free English stopword set. Extended enough to keep
# keyword output meaningful without pulling in NLTK.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an and are as at be by for from has have he her his i in is it its of on
    or that the this to was were will with you your our their they them we us
    but not no so if then than too very can could should would may might must
    do does did done being been about above after again against all am any
    because before below between both during each few further here how into
    itself more most other some such only own same off out over under up down
    what when where which who whom why while these those there their theirs he's
    she it'll i'm you're we're they're isn't aren't don't doesn't didn't won't
    also into per via etc get got make made just like use used using one two
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, punctuation stripped."""
    return _TOKEN_RE.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    """Tokens with stopwords and 1-character noise removed."""
    return [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1]


def ngrams(tokens: list[str], n: int) -> list[str]:
    """Contiguous n-grams as space-joined strings."""
    if n <= 1:
        return list(tokens)
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def phrase_candidates(text: str, *, max_n: int = 3) -> list[str]:
    """Unigrams..``max_n``-grams built from content tokens.

    N-grams are only kept when *every* member token is a content token, so we
    never emit phrases that straddle a stopword boundary (e.g. "shoes and").
    """
    toks = content_tokens(text)
    out: list[str] = list(toks)
    for n in range(2, max_n + 1):
        out.extend(ngrams(toks, n))
    return out


def term_frequencies(text: str, *, max_n: int = 3) -> Counter[str]:
    return Counter(phrase_candidates(text, max_n=max_n))


def tfidf_corpus(
    docs: Iterable[str], *, max_n: int = 3
) -> tuple[list[dict[str, float]], dict[str, int]]:
    """Compute TF-IDF vectors for a corpus.

    Returns ``(vectors, document_frequency)`` where each vector maps term ->
    tf-idf weight. IDF uses the smoothed ``ln((1 + N) / (1 + df)) + 1`` form so
    a term appearing in every document still carries a small positive weight.
    """
    doc_terms: list[Counter[str]] = [term_frequencies(d, max_n=max_n) for d in docs]
    n_docs = len(doc_terms)
    df: Counter[str] = Counter()
    for tf in doc_terms:
        df.update(tf.keys())

    vectors: list[dict[str, float]] = []
    for tf in doc_terms:
        total = sum(tf.values()) or 1
        vec: dict[str, float] = {}
        for term, count in tf.items():
            idf = math.log((1 + n_docs) / (1 + df[term])) + 1.0
            vec[term] = (count / total) * idf
        vectors.append(vec)
    return vectors, dict(df)


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity of two sparse term vectors. Range 0..1 for tf-idf."""
    if not a or not b:
        return 0.0
    # Iterate the smaller vector for the dot product.
    if len(a) > len(b):
        a, b = b, a
    dot = sum(w * b.get(term, 0.0) for term, w in a.items())
    if dot == 0.0:
        return 0.0
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Scale a mapping so its max value is 1.0 (no-op on empty/zero input)."""
    if not scores:
        return {}
    top = max(scores.values())
    if top <= 0:
        return {k: 0.0 for k in scores}
    return {k: v / top for k, v in scores.items()}
