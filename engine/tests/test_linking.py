from __future__ import annotations

from seo_engine import htmlutil
from seo_engine.linking import apply_links, plan_links, recommend_links
from seo_engine.models import Page
from seo_engine.safety import SafetyPolicy


def _site() -> list[Page]:
    pillar = Page(
        url="https://ex.com/running-shoes",
        html="<html><body><h1>Running Shoes</h1>"
        "<p>Everything about running shoes for marathon training.</p></body></html>",
        title="Running Shoes",
        text="Everything about running shoes for marathon training running shoes",
    )
    spoke = Page(
        url="https://ex.com/marathon-guide",
        html="<html><body><h1>Marathon Guide</h1>"
        "<p>Our marathon training plan pairs well with good running shoes for race day.</p>"
        "</body></html>",
        title="Marathon Guide",
        text="Our marathon training plan pairs well with good running shoes for race day",
    )
    return [pillar, spoke]


def test_recommend_links_finds_relevant_pair():
    recs = recommend_links(_site(), min_relevance=0.0)
    assert recs
    r = recs[0]
    assert r.source_url != r.target_url
    # anchor must be text that already exists on the source page
    src = next(p for p in _site() if p.url == r.source_url)
    assert r.anchor.lower() in src.text.lower()


def test_apply_links_inserts_anchor_and_preserves_text():
    site = _site()
    recs = recommend_links(site, min_relevance=0.0)
    # apply to the page that has a recommendation
    src_urls = {r.source_url for r in recs}
    page = next(p for p in site if p.url in src_urls)

    original_text = htmlutil.visible_text(page.html)
    cs = apply_links(page, recs)
    assert cs.applied >= 1
    # a real <a> now exists
    soup = htmlutil.parse(cs.new_html)
    assert soup.find("a", href=True) is not None
    # visible text is byte-for-byte preserved (only a link was wrapped)
    assert htmlutil.visible_text(cs.new_html) == original_text
    # change is reversible
    assert cs.revert() == page.html
    assert cs.validation is not None and cs.validation.ok


def test_blast_radius_cap_enforced():
    site = _site()
    recs = recommend_links(site, min_relevance=0.0, top_k_per_source=10)
    page = next(p for p in site if any(r.source_url == p.url for r in recs))
    policy = SafetyPolicy(max_links_per_page=1)
    plan = plan_links(page, recs, policy=policy)
    assert plan.blast_radius <= 1


def test_idempotent_no_duplicate_links():
    site = _site()
    recs = recommend_links(site, min_relevance=0.0)
    page = next(p for p in site if any(r.source_url == p.url for r in recs))
    cs1 = apply_links(page, recs)
    # feed the already-linked HTML back in; recommender should not re-link same target
    relinked = Page(url=page.url, html=cs1.new_html, title=page.title,
                    text=htmlutil.visible_text(cs1.new_html))
    site2 = [relinked if p.url == page.url else p for p in site]
    recs2 = recommend_links(site2, min_relevance=0.0)
    # no rec should target a URL already linked from the source
    existing = htmlutil.existing_link_targets(htmlutil.parse(cs1.new_html))
    for r in recs2:
        if r.source_url == page.url:
            assert r.target_url not in existing


def test_no_link_inside_existing_anchor_or_code():
    page = Page(
        url="https://ex.com/a",
        html="<html><body><p>See <a href='/x'>running shoes</a> and "
        "<code>running shoes</code> examples.</p></body></html>",
        text="See running shoes and running shoes examples",
    )
    other = Page(
        url="https://ex.com/running-shoes",
        html="<html><body><h1>Running Shoes</h1><p>running shoes hub</p></body></html>",
        title="Running Shoes",
        text="running shoes hub running shoes",
    )
    recs = recommend_links([page, other], min_relevance=0.0)
    cs = apply_links(page, recs)
    soup = htmlutil.parse(cs.new_html)
    # the <code> content must remain plain text, not wrapped in <a>
    code = soup.find("code")
    assert code is not None and code.find("a") is None
    # original anchor still points where it did
    assert soup.find("a", href="/x") is not None
