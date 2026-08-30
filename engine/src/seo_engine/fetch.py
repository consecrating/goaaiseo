"""Optional live fetching of pages (requires the ``fetch`` extra: httpx).

Kept separate and optional so the core engine runs fully offline on provided
HTML. This is the only place that touches the network, and it is polite by
default (custom UA, timeout, redirect limit).
"""

from __future__ import annotations

from . import htmlutil
from .models import Page

_USER_AGENT = "GOAAISEO-Engine/0.1 (+https://github.com/consecrating/goaaiseo)"


def fetch_page(url: str, *, timeout: float = 20.0) -> Page:
    """Fetch a single URL into a :class:`Page` (title + visible text + html).

    Raises a clear ImportError if httpx isn't installed.
    """
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "Live fetching needs the 'fetch' extra. Install with: "
            "pip install 'seo-engine[fetch]'"
        ) from exc

    with httpx.Client(
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        html = resp.text

    return Page(
        url=str(resp.url),
        html=html,
        title=htmlutil.extract_title(html),
        text=htmlutil.visible_text(html),
    )


def fetch_pages(urls: list[str], *, timeout: float = 20.0) -> list[Page]:
    """Fetch several URLs, skipping ones that error (best-effort corpus build)."""
    pages: list[Page] = []
    for url in urls:
        try:
            pages.append(fetch_page(url, timeout=timeout))
        except Exception:  # noqa: BLE001 - one bad URL shouldn't abort the run
            continue
    return pages
