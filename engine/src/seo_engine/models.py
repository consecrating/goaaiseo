"""Shared data models.

Everything crossing a module boundary is a typed dataclass, never a bare dict,
so the shapes are explicit and mistakes surface at the boundary instead of deep
inside HTML manipulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Page:
    """A single page under analysis.

    ``html`` is optional: keyword discovery only needs text, while linking and
    alt-text need the real markup to edit it safely.
    """

    url: str
    html: str = ""
    title: str = ""
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Keywords
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class KeywordStat:
    """A keyword/phrase and how strongly a corpus is *about* it."""

    keyword: str
    score: float          # relevance weight (tf-idf-derived, normalized 0..1)
    documents: int        # how many pages in the corpus use it
    occurrences: int      # total raw occurrences across the corpus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KeywordGap:
    """A keyword competitors rank/write for that you underuse or miss entirely."""

    keyword: str
    competitor_score: float
    own_score: float
    gap: float            # competitor_score - own_score (higher = bigger opportunity)
    competitor_documents: int
    status: str           # "missing" | "underused"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Internal linking
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LinkRec:
    """A recommended source -> target internal link."""

    source_url: str
    target_url: str
    anchor: str
    score: float
    relevance: float
    context_snippet: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Alt text
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AltTextRec:
    """A recommendation for one <img> element."""

    src: str
    current_alt: Optional[str]      # None = attribute absent, "" = present but empty
    suggested_alt: str
    action: str                     # "add" | "replace" | "keep" | "mark_decorative"
    issues: tuple[str, ...]         # why the current alt was flagged
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["issues"] = list(self.issues)
        return d


# --------------------------------------------------------------------------- #
# Safety: plans, change sets, validation
# --------------------------------------------------------------------------- #
@dataclass
class Plan:
    """A dry-run description of proposed edits to a single page.

    A plan never touches anything. It is produced first so a human or the
    autonomous agent can inspect exactly what *would* change before committing.
    """

    url: str
    kind: str                        # "linking" | "alttext"
    edits: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    blast_radius: int = 0            # number of edits that would be applied

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "kind": self.kind,
            "edits": self.edits,
            "skipped": self.skipped,
            "blast_radius": self.blast_radius,
        }


@dataclass
class ChangeSet:
    """The result of *applying* a plan — reversible by construction."""

    url: str
    kind: str
    applied: int
    original_html: str               # the revert payload
    new_html: str
    edits: list[dict[str, Any]] = field(default_factory=list)
    validation: "Optional[ValidationResult]" = None

    def revert(self) -> str:
        """Return the exact original HTML. Undo is always one call away."""
        return self.original_html

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "kind": self.kind,
            "applied": self.applied,
            "original_html": self.original_html,
            "new_html": self.new_html,
            "edits": self.edits,
            "validation": self.validation.to_dict() if self.validation else None,
        }


@dataclass(frozen=True)
class ValidationIssue:
    severity: str                    # "error" | "warning"
    code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
        }
