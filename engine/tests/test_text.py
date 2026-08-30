from __future__ import annotations

from seo_engine import text as t


def test_tokenize_and_content_tokens():
    assert t.tokenize("Hello, World! 123") == ["hello", "world", "123"]
    # stopwords + 1-char noise removed
    assert "the" not in t.content_tokens("the running shoes")
    assert t.content_tokens("the running shoes") == ["running", "shoes"]


def test_phrase_candidates_no_stopword_straddle():
    phrases = t.phrase_candidates("best running shoes for men", max_n=2)
    assert "running shoes" in phrases
    # "shoes for" must not appear because "for" is a stopword
    assert "shoes for" not in phrases


def test_tfidf_and_cosine_identical_docs():
    docs = ["running shoes trail", "running shoes trail"]
    vectors, df = t.tfidf_corpus(docs, max_n=1)
    assert df["running"] == 2
    assert abs(t.cosine(vectors[0], vectors[1]) - 1.0) < 1e-9


def test_cosine_orthogonal_docs():
    vectors, _ = t.tfidf_corpus(["apples oranges", "rockets engines"], max_n=1)
    assert t.cosine(vectors[0], vectors[1]) == 0.0


def test_normalize_scores():
    assert t.normalize_scores({"a": 2.0, "b": 1.0}) == {"a": 1.0, "b": 0.5}
    assert t.normalize_scores({}) == {}
