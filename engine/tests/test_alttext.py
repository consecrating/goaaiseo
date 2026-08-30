from __future__ import annotations

from seo_engine import htmlutil
from seo_engine.alttext import (
    MAX_ALT_LENGTH,
    apply_alt_text,
    audit_alt_text,
    recommend_alt_text,
)
from seo_engine.models import Page


def test_audit_flags_problems():
    assert "missing_alt_attribute" in audit_alt_text(None)
    assert "empty_alt" in audit_alt_text("")
    assert "redundant_prefix" in audit_alt_text("Image of a dog running")
    assert "too_long" in audit_alt_text("x" * (MAX_ALT_LENGTH + 1))
    assert "looks_like_filename" in audit_alt_text("DSC_0001.jpg")
    assert "keyword_stuffed" in audit_alt_text("shoes, running, trail, cheap, buy")
    assert audit_alt_text("A golden retriever catching a frisbee") == ()


def test_recommend_add_missing_alt_from_filename():
    page = Page(
        url="https://ex.com/p",
        html="<html><body><h2>Trail Gear</h2>"
        "<img src='/img/blue-running-shoes.jpg'></body></html>",
        title="Trail Gear",
    )
    recs = recommend_alt_text(page)
    assert len(recs) == 1
    r = recs[0]
    assert r.action == "add"
    assert r.current_alt is None
    assert "running shoes" in r.suggested_alt.lower()


def test_junk_filename_falls_back_to_context():
    # 'DSC_0042' is meaningless -> must NOT become the alt; use nearby heading.
    page = Page(
        url="https://ex.com/p",
        html="<html><body><h2>Trail Grip</h2><p>Grips wet rock.</p>"
        "<img src='/img/DSC_0042.jpg'></body></html>",
        title="Boots",
    )
    rec = recommend_alt_text(page)[0]
    assert rec.action == "add"
    assert rec.suggested_alt.lower() not in ("dsc", "")
    assert "trail grip" in rec.suggested_alt.lower()


def test_decorative_image_gets_empty_alt():
    page = Page(
        url="https://ex.com/p",
        html="<html><body><img src='/img/spacer.gif' width='1' height='1'></body></html>",
    )
    recs = recommend_alt_text(page)
    assert recs[0].action == "mark_decorative"
    assert recs[0].suggested_alt == ""


def test_good_alt_is_kept():
    page = Page(
        url="https://ex.com/p",
        html="<html><body><img src='/dog.jpg' alt='A happy dog in a park'></body></html>",
    )
    recs = recommend_alt_text(page)
    assert recs[0].action == "keep"


def test_apply_alt_writes_attribute_and_preserves_text():
    page = Page(
        url="https://ex.com/p",
        html="<html><body><h2>Mountain Boots</h2>"
        "<p>Great gear.</p><img src='/img/leather-boots.png'></body></html>",
        title="Mountain Boots",
    )
    before_text = htmlutil.visible_text(page.html)
    recs = recommend_alt_text(page)
    cs = apply_alt_text(page, recs)
    assert cs.applied == 1
    soup = htmlutil.parse(cs.new_html)
    img = soup.find("img")
    assert img.get("alt")  # non-empty alt now present
    # visible text unchanged (alt is an attribute, not visible text)
    assert htmlutil.visible_text(cs.new_html) == before_text
    # reversible
    assert cs.revert() == page.html
    assert cs.validation is not None and cs.validation.ok


def test_apply_alt_empty_for_decorative_is_valid():
    page = Page(
        url="https://ex.com/p",
        html="<html><body><img src='/img/divider.png'></body></html>",
    )
    recs = recommend_alt_text(page)
    cs = apply_alt_text(page, recs)
    soup = htmlutil.parse(cs.new_html)
    img = soup.find("img")
    assert img.has_attr("alt") and img["alt"] == ""
