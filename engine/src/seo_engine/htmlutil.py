"""Safe HTML helpers built on BeautifulSoup + lxml.

Every edit in this engine goes through a real DOM parser. We never build links
or rewrite attributes with regex/string concatenation, because that is exactly
how automated tools corrupt markup (unbalanced tags, broken entities, injected
angle brackets). Parse -> mutate nodes -> serialize.
"""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Comment, NavigableString, Tag

# Containers whose text should never be turned into anchors or scanned for
# link insertion — editing inside these breaks pages or changes meaning.
SKIP_ANCESTORS: frozenset[str] = frozenset(
    {"a", "script", "style", "code", "pre", "kbd", "textarea", "head", "title"}
)

# Tags whose inner text is "real content" we can safely read/link within.
CONTENT_TAGS: tuple[str, ...] = ("p", "li", "span", "em", "strong", "div")


def parse(html: str) -> BeautifulSoup:
    """Parse with lxml (fast, lenient, well-formed output)."""
    return BeautifulSoup(html, "lxml")


def serialize(soup: BeautifulSoup) -> str:
    return str(soup)


def visible_text(html_or_soup) -> str:
    """Concatenated visible text, excluding script/style and comments.

    Used both for keyword extraction and, crucially, for the safety check that
    verifies an edit did not delete or reorder human-readable content.
    """
    soup = html_or_soup if isinstance(html_or_soup, BeautifulSoup) else parse(html_or_soup)
    parts: list[str] = []
    for node in soup.descendants:
        if isinstance(node, Comment):
            continue
        if isinstance(node, NavigableString):
            parent = node.parent
            if parent is not None and parent.name in {"script", "style"}:
                continue
            parts.append(str(node))
    return " ".join(" ".join(parts).split())


def extract_title(html_or_soup) -> str:
    soup = html_or_soup if isinstance(html_or_soup, BeautifulSoup) else parse(html_or_soup)
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return ""


def in_skip_zone(node: Tag) -> bool:
    """True if the node is inside an element we must not edit within."""
    for parent in node.parents:
        if isinstance(parent, Tag) and parent.name in SKIP_ANCESTORS:
            return True
    return False


def existing_link_targets(soup: BeautifulSoup) -> set[str]:
    """All hrefs already present, so we never create a duplicate link."""
    out: set[str] = set()
    for a in soup.find_all("a", href=True):
        out.add(a["href"].strip())
    return out


def nearest_heading_text(img: Tag) -> Optional[str]:
    """Closest preceding heading text — useful context for alt-text drafting."""
    for prev in img.find_all_previous(["h1", "h2", "h3", "h4"]):
        txt = prev.get_text(strip=True)
        if txt:
            return txt
    return None


def surrounding_text(node: Tag, *, max_chars: int = 240) -> str:
    """Text of the node's nearest block ancestor, trimmed."""
    block = node
    for parent in node.parents:
        if isinstance(parent, Tag) and parent.name in {"p", "li", "figure", "div", "section"}:
            block = parent
            break
    txt = block.get_text(" ", strip=True) if isinstance(block, Tag) else ""
    return txt[:max_chars]
