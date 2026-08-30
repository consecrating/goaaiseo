"""GOAAISEO engine — real, runnable implementations of the blueprint's core levers.

Four capabilities, one safety contract:

1. ``keywords``  — competitive keyword discovery + gap analysis (content-based).
2. ``linking``   — auto internal-linking recommendations + safe HTML application.
3. ``alttext``   — proper alt-text generation + validation + safe HTML application.
4. ``safety``    — the "no blunder" layer: dry-run first, validate, cap blast
   radius, and keep a revert payload for every change.

Design principles (why this won't quietly break a site):

* Nothing mutates a live system. Modules return *plans*; applying a plan is a
  separate, explicit call that produces a :class:`~seo_engine.models.ChangeSet`
  carrying the original HTML for one-call revert.
* HTML is edited through a real DOM parser (BeautifulSoup + lxml), never via
  string/regex surgery. Every applied change is re-validated: the document must
  still parse and the visible text must be preserved.
"""

from __future__ import annotations

from .models import (
    AltTextRec,
    ChangeSet,
    KeywordGap,
    KeywordStat,
    LinkRec,
    Page,
    Plan,
    ValidationIssue,
    ValidationResult,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Page",
    "KeywordStat",
    "KeywordGap",
    "LinkRec",
    "AltTextRec",
    "Plan",
    "ChangeSet",
    "ValidationIssue",
    "ValidationResult",
]
