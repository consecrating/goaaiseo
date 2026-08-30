"""The "no blunder" layer.

No software can literally guarantee zero mistakes. What we *can* guarantee is a
discipline that makes damaging, silent changes structurally hard:

* **Dry-run first** — planners produce a :class:`Plan`; nothing mutates until an
  explicit apply step.
* **Blast-radius caps** — a hard ceiling on edits per page.
* **Reversibility** — every :class:`ChangeSet` carries the original HTML.
* **Post-edit validation** — after applying, the document must still parse and
  its visible text must be preserved (we only *add* links/attributes, never
  remove or reorder human-readable content). If validation fails, the caller
  gets the original HTML back untouched.

These checks are centralized here so every module inherits the same guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import htmlutil
from .models import ValidationIssue, ValidationResult

# Conservative defaults. Callers may tighten, not silently exceed.
DEFAULT_MAX_LINKS_PER_PAGE = 5
DEFAULT_MAX_ALT_EDITS_PER_PAGE = 100  # accessibility fixes are low-risk; allow many
DEFAULT_MAX_LINKS_PER_TARGET = 1      # never point at the same target twice from one page


@dataclass(frozen=True)
class SafetyPolicy:
    """Per-run limits. Immutable so a run cannot drift mid-flight."""

    max_links_per_page: int = DEFAULT_MAX_LINKS_PER_PAGE
    max_alt_edits_per_page: int = DEFAULT_MAX_ALT_EDITS_PER_PAGE
    max_links_per_target: int = DEFAULT_MAX_LINKS_PER_TARGET
    preserve_text: bool = True        # visible text must be identical after edit
    require_valid_html: bool = True


def _normalize_text(text: str) -> str:
    """Collapse whitespace so cosmetic reflow doesn't read as content loss."""
    return " ".join(text.split())


def validate_edit(
    original_html: str,
    new_html: str,
    *,
    policy: SafetyPolicy,
    expect_text_delta: str = "",
) -> ValidationResult:
    """Verify an edited document is safe to ship.

    ``expect_text_delta`` is any text we intentionally added as visible content
    (e.g. an anchor whose text did not previously exist verbatim). It is allowed
    to appear in the new visible text; everything else must be preserved.
    """
    issues: list[ValidationIssue] = []

    # 1. The new markup must still parse into a non-empty document.
    try:
        new_soup = htmlutil.parse(new_html)
    except Exception as exc:  # pragma: no cover - lxml is extremely lenient
        issues.append(
            ValidationIssue("error", "unparseable", f"Edited HTML failed to parse: {exc}")
        )
        return ValidationResult(ok=False, issues=issues)

    if policy.require_valid_html and new_soup.find() is None and new_html.strip():
        issues.append(
            ValidationIssue("error", "empty_dom", "Edited HTML parsed to an empty document.")
        )

    # 2. Visible text must be preserved (we only add links/attributes).
    if policy.preserve_text:
        before = _normalize_text(htmlutil.visible_text(original_html))
        after = _normalize_text(htmlutil.visible_text(new_html))
        # Adding an anchor reuses existing text, so `after` should equal `before`.
        # Any intentionally added visible text is whitelisted via expect_text_delta.
        if after != before:
            stripped = after
            for token in _normalize_text(expect_text_delta).split():
                stripped = stripped.replace(token, "", 1)
            if _normalize_text(stripped) != before:
                issues.append(
                    ValidationIssue(
                        "error",
                        "text_changed",
                        "Visible text changed beyond the intended addition — "
                        "refusing to apply.",
                    )
                )

    # 3. No <script> should have been introduced by our edit.
    if len(htmlutil.parse(original_html).find_all("script")) < len(new_soup.find_all("script")):
        issues.append(
            ValidationIssue("error", "script_injected", "Edit introduced a new <script> tag.")
        )

    ok = not any(i.severity == "error" for i in issues)
    return ValidationResult(ok=ok, issues=issues)
