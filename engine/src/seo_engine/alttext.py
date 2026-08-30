"""Proper alt text: audit existing alt attributes and generate better ones.

"Proper" here follows accessibility + SEO consensus (WCAG 1.1.1, WAI image
tutorial):

* Every meaningful <img> needs a concise, descriptive alt.
* Decorative images should have an *empty* alt (``alt=""``) so screen readers
  skip them — never a keyword dump.
* Alt text should be under ~125 characters, must not start with "image of" /
  "picture of", must not be the raw filename, and must not be keyword-stuffed.

Honest scope: without a vision model we cannot *see* the image, so generated
alt text is derived from real page context — filename, nearby heading, caption,
figure text, and page title. This produces genuinely useful, human-editable
drafts and, more importantly, reliably *flags* the alt problems that hurt
accessibility and SEO. Each rec carries a ``confidence`` so a human/agent can
decide what to auto-apply vs. review.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from . import htmlutil
from .models import AltTextRec, ChangeSet, Page, Plan
from .safety import SafetyPolicy, validate_edit

MAX_ALT_LENGTH = 125
_BAD_PREFIXES = ("image of", "picture of", "photo of", "graphic of", "image showing")
_STUFFING_SEPARATORS = re.compile(r"[|,]{1}")
_FILENAME_JUNK = re.compile(r"[-_]+")
_DECORATIVE_HINTS = ("spacer", "divider", "bg", "background", "decoration", "shim", "pixel")
# Generic camera / CMS filename stems that carry no descriptive meaning.
_JUNK_FILENAME_TOKENS = frozenset(
    {"dsc", "dscn", "img", "image", "photo", "pic", "untitled", "screenshot",
     "scan", "capture", "final", "copy", "edit", "download", "unnamed"}
)


def _humanize_filename(src: str) -> str:
    """Turn 'blue-running-shoes_v2.jpg' into 'blue running shoes'.

    Returns "" when the filename is generic junk (e.g. 'DSC_0042', 'IMG1234'),
    so the caller falls back to real page context instead of a meaningless alt.
    """
    name = PurePosixPath(src.split("?")[0]).stem
    name = _FILENAME_JUNK.sub(" ", name)
    name = re.sub(r"\b\d{2,4}x\d{2,4}\b", "", name)  # drop dimensions like 1200x800
    name = re.sub(r"\bv?\d+\b", "", name)            # drop version/size tokens
    # Split camera prefixes glued to digits, e.g. "IMG1234" -> "IMG".
    tokens = [tok for tok in re.split(r"[^a-zA-Z]+", name) if tok]
    meaningful = [tok for tok in tokens if tok.lower() not in _JUNK_FILENAME_TOKENS and len(tok) > 1]
    if not meaningful:
        return ""
    return " ".join(meaningful).strip()


def _looks_decorative(src: str, width: str | None, height: str | None) -> bool:
    low = src.lower()
    if any(h in low for h in _DECORATIVE_HINTS):
        return True
    try:
        if width is not None and height is not None:
            if int(width) <= 3 or int(height) <= 3:  # 1x1 tracking pixels etc.
                return True
    except ValueError:
        pass
    return False


def audit_alt_text(text_or_alt: str | None) -> tuple[str, ...]:
    """Return the set of problems with an existing alt value."""
    issues: list[str] = []
    if text_or_alt is None:
        issues.append("missing_alt_attribute")
        return tuple(issues)

    alt = text_or_alt.strip()
    if alt == "":
        # Empty alt is valid *only* for decorative images; caller decides.
        issues.append("empty_alt")
        return tuple(issues)

    low = alt.lower()
    if any(low.startswith(p) for p in _BAD_PREFIXES):
        issues.append("redundant_prefix")
    if len(alt) > MAX_ALT_LENGTH:
        issues.append("too_long")
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg)$", low):
        issues.append("looks_like_filename")
    if len(_STUFFING_SEPARATORS.findall(alt)) >= 2:
        issues.append("keyword_stuffed")
    words = low.split()
    if words and len(set(words)) <= max(1, len(words) // 3):
        issues.append("repetitive")
    return tuple(issues)


def _generate_alt(*, src: str, heading: str | None, context: str, title: str) -> tuple[str, float]:
    """Draft alt text from available page context. Returns (alt, confidence)."""
    from_name = _humanize_filename(src)
    candidates: list[tuple[str, float]] = []

    if from_name and len(from_name) >= 3 and not from_name.isdigit():
        candidates.append((from_name, 0.6))
    if heading:
        candidates.append((heading.strip(), 0.5))
    if context:
        # First sentence-ish chunk of surrounding text.
        chunk = re.split(r"(?<=[.!?])\s", context.strip())[0]
        if 3 <= len(chunk) <= MAX_ALT_LENGTH:
            candidates.append((chunk, 0.45))
    if title:
        candidates.append((title.strip(), 0.35))

    if not candidates:
        return "", 0.0

    # Prefer the highest-confidence candidate that is a sensible length.
    candidates.sort(key=lambda c: -c[1])
    for alt, conf in candidates:
        alt = " ".join(alt.split())
        if len(alt) > MAX_ALT_LENGTH:
            alt = alt[:MAX_ALT_LENGTH].rsplit(" ", 1)[0]
        if len(alt) >= 3:
            return alt, conf
    return "", 0.0


def recommend_alt_text(page: Page) -> list[AltTextRec]:
    """Produce an alt-text recommendation for every <img> on the page."""
    if not page.html:
        return []
    soup = htmlutil.parse(page.html)
    title = page.title or htmlutil.extract_title(soup)
    recs: list[AltTextRec] = []

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        raw_alt = img.get("alt")  # None if attribute absent
        current_alt = raw_alt if raw_alt is None else str(raw_alt)
        issues = audit_alt_text(current_alt)

        decorative = _looks_decorative(src, img.get("width"), img.get("height"))
        if decorative:
            # Correct fix for decorative images is an explicit empty alt.
            action = "keep" if current_alt == "" else "mark_decorative"
            recs.append(
                AltTextRec(
                    src=src, current_alt=current_alt, suggested_alt="",
                    action=action, issues=issues, confidence=0.7,
                )
            )
            continue

        heading = htmlutil.nearest_heading_text(img)
        context = htmlutil.surrounding_text(img)
        # A figure caption, if present, is the best signal.
        caption = None
        fig = img.find_parent("figure")
        if fig:
            cap = fig.find("figcaption")
            if cap:
                caption = cap.get_text(" ", strip=True)
        suggested, confidence = _generate_alt(
            src=src, heading=caption or heading, context=context, title=title
        )

        has_good_alt = current_alt not in (None, "") and not issues
        if has_good_alt:
            action = "keep"
            suggested = str(current_alt)
            confidence = 1.0
        elif current_alt in (None, ""):
            action = "add"
        else:
            action = "replace"

        recs.append(
            AltTextRec(
                src=src, current_alt=current_alt, suggested_alt=suggested,
                action=action, issues=issues, confidence=round(confidence, 3),
            )
        )
    return recs


def plan_alt_text(
    page: Page, recs: list[AltTextRec], *, policy: SafetyPolicy | None = None
) -> Plan:
    """Dry-run: which <img> alts would change, and how."""
    policy = policy or SafetyPolicy()
    plan = Plan(url=page.url, kind="alttext")
    for r in recs:
        if r.action in ("add", "replace", "mark_decorative"):
            if plan.blast_radius >= policy.max_alt_edits_per_page:
                plan.skipped.append({**r.to_dict(), "reason": "blast_radius_cap_reached"})
                continue
            if r.action in ("add", "replace") and not r.suggested_alt:
                plan.skipped.append({**r.to_dict(), "reason": "no_confident_suggestion"})
                continue
            plan.edits.append(r.to_dict())
            plan.blast_radius += 1
        else:
            plan.skipped.append({**r.to_dict(), "reason": "already_ok"})
    return plan


def apply_alt_text(
    page: Page, recs: list[AltTextRec], *, policy: SafetyPolicy | None = None
) -> ChangeSet:
    """Write alt attributes into the real DOM and return a reversible ChangeSet.

    Alt edits never touch visible text, so the safety validator's text-preserved
    check must pass exactly.
    """
    policy = policy or SafetyPolicy()
    original = page.html
    plan = plan_alt_text(page, recs, policy=policy)

    if not page.html or not plan.edits:
        return ChangeSet(
            url=page.url, kind="alttext", applied=0,
            original_html=original, new_html=original, edits=[],
        )

    soup = htmlutil.parse(page.html)
    # Index edits by src for direct lookup.
    by_src: dict[str, dict] = {}
    for e in plan.edits:
        by_src.setdefault(e["src"], e)

    applied_edits: list[dict] = []
    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        edit = by_src.get(src)
        if edit is None:
            continue
        img["alt"] = edit["suggested_alt"]  # "" for decorative is correct
        applied_edits.append(edit)
        del by_src[src]  # one edit per src

    new_html = htmlutil.serialize(soup)
    validation = validate_edit(original, new_html, policy=policy, expect_text_delta="")

    if not validation.ok:
        return ChangeSet(
            url=page.url, kind="alttext", applied=0,
            original_html=original, new_html=original,
            edits=[], validation=validation,
        )

    return ChangeSet(
        url=page.url, kind="alttext", applied=len(applied_edits),
        original_html=original, new_html=new_html,
        edits=applied_edits, validation=validation,
    )
