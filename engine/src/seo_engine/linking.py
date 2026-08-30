"""Auto internal-linking: recommend high-value links and apply them safely.

Two phases, mirroring the blueprint's Phase 9 but runnable today:

1. :func:`recommend_links` — scores every candidate source->target pair on
   semantic relevance (TF-IDF cosine), target need (under-linked pages get a
   boost), and finds a natural anchor phrase already present in the source text.
2. :func:`plan_links` / :func:`apply_links` — turn recommendations for one page
   into a dry-run :class:`Plan`, then (only on explicit apply) insert anchors in
   the real DOM, validate, and return a reversible :class:`ChangeSet`.

Anchors are only ever created from text that *already exists* on the source
page, so we never fabricate visible copy — which keeps the safety validator's
"text preserved" check satisfied.
"""

from __future__ import annotations

import re
from collections import Counter

from . import htmlutil
from . import text as textmod
from .models import ChangeSet, LinkRec, Page, Plan
from .safety import SafetyPolicy, validate_edit

# Scoring weights (tunable; documented in the blueprint's 9.4).
_W_RELEVANCE = 0.6
_W_TARGET_NEED = 0.25
_W_AUTHORITY = 0.15


def _inlink_counts(pages: list[Page]) -> Counter[str]:
    """How many internal inbound links each page already has (need signal)."""
    urls = {p.url for p in pages}
    counts: Counter[str] = Counter({p.url: 0 for p in pages})
    for p in pages:
        if not p.html:
            continue
        soup = htmlutil.parse(p.html)
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href in urls and href != p.url:
                counts[href] += 1
    return counts


def _find_anchor(source_text: str, target_keywords: list[str]) -> tuple[str, str]:
    """Find an existing phrase in ``source_text`` to use as the anchor.

    Returns ``(anchor, context_snippet)``. Prefers the longest target keyword
    that literally occurs in the source (case-insensitive), so the anchor is
    both relevant and already-present. Empty anchor means "no safe anchor".
    """
    lowered = source_text.lower()
    for kw in sorted(target_keywords, key=len, reverse=True):
        if len(kw) < 3:
            continue
        idx = lowered.find(kw)
        if idx == -1:
            continue
        # Recover the original-case substring for a natural anchor.
        anchor = source_text[idx : idx + len(kw)]
        start = max(0, idx - 60)
        end = min(len(source_text), idx + len(kw) + 60)
        snippet = source_text[start:end].strip()
        return anchor, snippet
    return "", ""


def recommend_links(
    pages: list[Page],
    *,
    max_n: int = 3,
    top_k_per_source: int = 3,
    min_relevance: float = 0.05,
) -> list[LinkRec]:
    """Rank source->target internal link opportunities across a page set."""
    usable = [p for p in pages if (p.text or p.html)]
    if len(usable) < 2:
        return []

    # Ensure every page has text to work from (fall back to HTML visible text).
    resolved: list[Page] = []
    for p in usable:
        txt = p.text or (htmlutil.visible_text(p.html) if p.html else "")
        title = p.title or (htmlutil.extract_title(p.html) if p.html else "")
        resolved.append(Page(url=p.url, html=p.html, title=title, text=txt))

    docs = [p.text for p in resolved]
    vectors, _ = textmod.tfidf_corpus(docs, max_n=max_n)
    inlinks = _inlink_counts(resolved)
    max_inlinks = max(inlinks.values()) if inlinks else 0

    # Per-target top keywords, used to source natural anchors.
    target_keywords: dict[str, list[str]] = {}
    for i, p in enumerate(resolved):
        top_terms = sorted(vectors[i].items(), key=lambda kv: -kv[1])[:12]
        kws = [t for t, _ in top_terms]
        # Title words are strong anchor candidates too.
        kws.extend(textmod.content_tokens(p.title))
        target_keywords[p.url] = kws

    recs: list[LinkRec] = []
    for i, src in enumerate(resolved):
        src_soup = htmlutil.parse(src.html) if src.html else None
        already_linked = htmlutil.existing_link_targets(src_soup) if src_soup else set()

        scored: list[LinkRec] = []
        for j, tgt in enumerate(resolved):
            if src.url == tgt.url:
                continue
            if tgt.url in already_linked:
                continue  # idempotent: don't re-recommend an existing link

            relevance = textmod.cosine(vectors[i], vectors[j])
            if relevance < min_relevance:
                continue

            need = 1.0 - (inlinks[tgt.url] / max_inlinks) if max_inlinks else 1.0
            authority = (sum(vectors[i].values()) / (1 + len(vectors[i]))) if vectors[i] else 0.0
            authority = min(authority, 1.0)

            anchor, snippet = _find_anchor(src.text, target_keywords[tgt.url])
            if not anchor:
                continue  # no safe, pre-existing anchor -> skip (no fabrication)

            score = (
                _W_RELEVANCE * relevance
                + _W_TARGET_NEED * need
                + _W_AUTHORITY * authority
            )
            scored.append(
                LinkRec(
                    source_url=src.url,
                    target_url=tgt.url,
                    anchor=anchor,
                    score=round(score, 6),
                    relevance=round(relevance, 6),
                    context_snippet=snippet,
                    rationale=(
                        f"relevance={relevance:.2f}, target_need={need:.2f} "
                        f"(inlinks={inlinks[tgt.url]}), anchor found in source text"
                    ),
                )
            )

        # De-duplicate anchors within a source (avoid over-optimization).
        scored.sort(key=lambda r: (-r.score, r.target_url))
        seen_anchors: set[str] = set()
        kept: list[LinkRec] = []
        for r in scored:
            key = r.anchor.lower()
            if key in seen_anchors:
                continue
            seen_anchors.add(key)
            kept.append(r)
            if len(kept) >= top_k_per_source:
                break
        recs.extend(kept)

    recs.sort(key=lambda r: (-r.score, r.source_url, r.target_url))
    return recs


def plan_links(
    page: Page,
    recs: list[LinkRec],
    *,
    policy: SafetyPolicy | None = None,
) -> Plan:
    """Dry-run: what links *would* be inserted into ``page`` (no mutation)."""
    policy = policy or SafetyPolicy()
    plan = Plan(url=page.url, kind="linking")

    page_recs = [r for r in recs if r.source_url == page.url]
    per_target: Counter[str] = Counter()
    for r in page_recs:
        reason = _rejection_reason(page, r, per_target, plan.blast_radius, policy)
        if reason:
            plan.skipped.append({**r.to_dict(), "reason": reason})
            continue
        per_target[r.target_url] += 1
        plan.edits.append(r.to_dict())
        plan.blast_radius += 1
    return plan


def _rejection_reason(
    page: Page,
    rec: LinkRec,
    per_target: Counter[str],
    blast: int,
    policy: SafetyPolicy,
) -> str:
    if blast >= policy.max_links_per_page:
        return "blast_radius_cap_reached"
    if per_target[rec.target_url] >= policy.max_links_per_target:
        return "target_link_cap_reached"
    if page.html and rec.anchor.lower() not in page.html.lower():
        return "anchor_not_found_in_html"
    return ""


def apply_links(
    page: Page,
    recs: list[LinkRec],
    *,
    policy: SafetyPolicy | None = None,
) -> ChangeSet:
    """Apply the planned links to the real DOM and return a reversible ChangeSet.

    Only the first textual occurrence of each anchor is linked, and never inside
    an existing <a>, heading, script/style, or code block. If post-edit
    validation fails, the original HTML is returned unchanged.
    """
    policy = policy or SafetyPolicy()
    original = page.html
    plan = plan_links(page, recs, policy=policy)

    if not page.html or not plan.edits:
        return ChangeSet(
            url=page.url, kind="linking", applied=0,
            original_html=original, new_html=original, edits=[],
        )

    soup = htmlutil.parse(page.html)
    applied_edits: list[dict] = []

    for edit in plan.edits:
        anchor = edit["anchor"]
        target = edit["target_url"]
        if _insert_one_link(soup, anchor=anchor, href=target):
            applied_edits.append(edit)

    new_html = htmlutil.serialize(soup)
    validation = validate_edit(original, new_html, policy=policy, expect_text_delta="")

    if not validation.ok:
        # Refuse to ship a broken edit. Hand back the pristine original.
        return ChangeSet(
            url=page.url, kind="linking", applied=0,
            original_html=original, new_html=original,
            edits=[], validation=validation,
        )

    return ChangeSet(
        url=page.url, kind="linking", applied=len(applied_edits),
        original_html=original, new_html=new_html,
        edits=applied_edits, validation=validation,
    )


def _insert_one_link(soup, *, anchor: str, href: str) -> bool:
    """Wrap the first safe textual occurrence of ``anchor`` in an <a href>.

    Returns True if a link was inserted. Splits the text node so surrounding
    text is preserved exactly.
    """
    from bs4.element import NavigableString, Tag

    pattern = re.compile(re.escape(anchor), re.IGNORECASE)

    for node in list(soup.find_all(string=True)):
        if not isinstance(node, NavigableString):
            continue
        parent = node.parent
        if not isinstance(parent, Tag):
            continue
        if htmlutil.in_skip_zone(parent):
            continue
        text = str(node)
        m = pattern.search(text)
        if not m:
            continue

        before, matched, after = text[: m.start()], text[m.start() : m.end()], text[m.end() :]
        a = soup.new_tag("a", href=href)
        a.string = matched

        new_nodes: list = []
        if before:
            new_nodes.append(NavigableString(before))
        new_nodes.append(a)
        if after:
            new_nodes.append(NavigableString(after))

        node.replace_with(*new_nodes)
        return True
    return False
