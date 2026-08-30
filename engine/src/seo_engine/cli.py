"""Command-line interface for the GOAAISEO engine.

Subcommands:
    keywords   discover competitive keywords / keyword gaps
    links      recommend (and optionally apply) internal links
    alt        audit + generate proper alt text

Every command is dry-run by default. Applying HTML changes requires the
explicit ``--apply`` flag *and* writes to a new file (never in place unless
``--in-place`` is passed), so the tool cannot silently overwrite your content.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, alttext, keywords, linking
from .htmlutil import extract_title, visible_text
from .models import Page
from .safety import SafetyPolicy


def _read_page(path_or_url: str, *, timeout: float = 20.0) -> Page:
    """Load a Page from a local file path or (with the fetch extra) a URL."""
    if path_or_url.startswith(("http://", "https://")):
        from .fetch import fetch_page

        return fetch_page(path_or_url, timeout=timeout)
    p = Path(path_or_url).resolve()
    html = p.read_text(encoding="utf-8")
    return Page(url=p.as_uri(), html=html, title=extract_title(html), text=visible_text(html))


def _load_pages(paths: list[str], *, timeout: float = 20.0) -> list[Page]:
    return [_read_page(x, timeout=timeout) for x in paths]


def _emit(data: object, *, out: str | None) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


# --------------------------------------------------------------------------- #
# keywords
# --------------------------------------------------------------------------- #
def _cmd_keywords(args: argparse.Namespace) -> int:
    competitors = _load_pages(args.competitors, timeout=args.timeout)
    if args.own:
        own = _load_pages(args.own, timeout=args.timeout)
        gaps = keywords.find_keyword_gaps(
            competitor_pages=competitors, own_pages=own,
            top_k=args.top_k, max_n=args.max_ngram,
        )
        _emit({"mode": "gap", "gaps": [g.to_dict() for g in gaps]}, out=args.out)
    else:
        stats = keywords.discover_keywords(
            competitors, top_k=args.top_k, max_n=args.max_ngram
        )
        _emit({"mode": "discover", "keywords": [s.to_dict() for s in stats]}, out=args.out)
    return 0


# --------------------------------------------------------------------------- #
# links
# --------------------------------------------------------------------------- #
def _cmd_links(args: argparse.Namespace) -> int:
    pages = _load_pages(args.pages, timeout=args.timeout)
    recs = linking.recommend_links(
        pages, top_k_per_source=args.per_page, min_relevance=args.min_relevance
    )
    policy = SafetyPolicy(max_links_per_page=args.max_links)

    if not args.apply:
        result = {
            "mode": "recommend",
            "recommendations": [r.to_dict() for r in recs],
            "plans": [linking.plan_links(p, recs, policy=policy).to_dict() for p in pages],
        }
        _emit(result, out=args.out)
        return 0

    changes = []
    for page in pages:
        cs = linking.apply_links(page, recs, policy=policy)
        if cs.applied and args.write_dir:
            _write_change(cs, args.write_dir)
        changes.append(cs.to_dict())
    _emit({"mode": "apply", "changes": changes}, out=args.out)
    return 0


# --------------------------------------------------------------------------- #
# alt
# --------------------------------------------------------------------------- #
def _cmd_alt(args: argparse.Namespace) -> int:
    pages = _load_pages(args.pages, timeout=args.timeout)
    policy = SafetyPolicy()

    if not args.apply:
        result = []
        for page in pages:
            recs = alttext.recommend_alt_text(page)
            result.append(
                {
                    "url": page.url,
                    "recommendations": [r.to_dict() for r in recs],
                    "plan": alttext.plan_alt_text(page, recs, policy=policy).to_dict(),
                }
            )
        _emit({"mode": "audit", "pages": result}, out=args.out)
        return 0

    changes = []
    for page in pages:
        recs = alttext.recommend_alt_text(page)
        cs = alttext.apply_alt_text(page, recs, policy=policy)
        if cs.applied and args.write_dir:
            _write_change(cs, args.write_dir)
        changes.append(cs.to_dict())
    _emit({"mode": "apply", "changes": changes}, out=args.out)
    return 0


def _write_change(change, write_dir: str) -> None:
    """Persist edited HTML to a new file; never overwrites the source in place."""
    d = Path(write_dir)
    d.mkdir(parents=True, exist_ok=True)
    stem = Path(change.url.replace("://", "_").replace("/", "_")).name or "page"
    (d / f"{stem}.{change.kind}.html").write_text(change.new_html, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="seo-engine",
        description="GOAAISEO engine: keywords, internal links, and alt text — safely.",
    )
    p.add_argument("--version", action="version", version=f"seo-engine {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    common_timeout = dict(type=float, default=20.0, help="Fetch timeout (s) for URLs")

    kw = sub.add_parser("keywords", help="Discover competitive keywords / gaps")
    kw.add_argument("competitors", nargs="+", help="Competitor page files or URLs")
    kw.add_argument("--own", nargs="*", default=None, help="Your own pages (enables gap mode)")
    kw.add_argument("--top-k", type=int, default=50)
    kw.add_argument("--max-ngram", type=int, default=3)
    kw.add_argument("--timeout", **common_timeout)
    kw.add_argument("--out", default=None, help="Write JSON here instead of stdout")
    kw.set_defaults(func=_cmd_keywords)

    ln = sub.add_parser("links", help="Recommend / apply internal links")
    ln.add_argument("pages", nargs="+", help="Page files or URLs in the site")
    ln.add_argument("--per-page", type=int, default=3)
    ln.add_argument("--min-relevance", type=float, default=0.05)
    ln.add_argument("--max-links", type=int, default=5, help="Blast-radius cap per page")
    ln.add_argument("--apply", action="store_true", help="Actually insert links (else dry-run)")
    ln.add_argument("--write-dir", default=None, help="Dir to write edited HTML (with --apply)")
    ln.add_argument("--timeout", **common_timeout)
    ln.add_argument("--out", default=None)
    ln.set_defaults(func=_cmd_links)

    al = sub.add_parser("alt", help="Audit + generate proper alt text")
    al.add_argument("pages", nargs="+", help="Page files or URLs")
    al.add_argument("--apply", action="store_true", help="Actually write alt attrs (else audit)")
    al.add_argument("--write-dir", default=None, help="Dir to write edited HTML (with --apply)")
    al.add_argument("--timeout", **common_timeout)
    al.add_argument("--out", default=None)
    al.set_defaults(func=_cmd_alt)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
