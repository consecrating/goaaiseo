# GOAAISEO Engine

A **real, runnable** implementation of three of the blueprint's highest-value
levers, wrapped in a safety layer designed to make automated HTML changes hard
to get catastrophically wrong.

| Capability | What it does | Module |
|---|---|---|
| **Competitive keyword discovery** | TF-IDF over competitor content + gap analysis vs. your own pages | `seo_engine.keywords` |
| **Auto internal-linking** | Scores source→target link opportunities, generates natural anchors, inserts them into real DOM | `seo_engine.linking` |
| **Proper alt text** | Audits existing `alt` attributes and generates accessible, non-stuffed alternatives | `seo_engine.alttext` |
| **Safety ("no blunder") layer** | Dry-run first, blast-radius caps, post-edit validation, one-call revert | `seo_engine.safety` |

---

## Install

```bash
cd engine
pip install -e .            # core (offline, works on provided HTML)
pip install -e '.[fetch]'   # + live URL fetching (httpx)
pip install -e '.[dev]'     # + pytest
```

## CLI

Everything is **dry-run by default**. HTML is only modified with `--apply`, and
even then output is written to a *new* directory — the tool never overwrites
your source files.

```bash
# 1. Competitive keywords — what competitors emphasize that you miss
seo-engine keywords competitor_a.html competitor_b.html --own my_page.html

# 2. Internal links — recommend (dry-run) then apply to a new dir
seo-engine links page1.html page2.html page3.html
seo-engine links page1.html page2.html --apply --write-dir ./edited

# 3. Proper alt text — audit then apply
seo-engine alt page.html
seo-engine alt page.html --apply --write-dir ./edited
```

Files or URLs are both accepted (URLs need the `fetch` extra).

## Library

```python
from seo_engine.models import Page
from seo_engine import keywords, linking, alttext
from seo_engine.safety import SafetyPolicy

pages = [Page(url="...", html="<html>...</html>", text="...")]

gaps  = keywords.find_keyword_gaps(competitor_pages=comp, own_pages=mine)
recs  = linking.recommend_links(pages)
change = linking.apply_links(pages[0], recs, policy=SafetyPolicy(max_links_per_page=3))

if change.applied:
    deploy(change.new_html)        # ship it
    # ...or undo instantly:
    original = change.revert()
```

---

## The safety contract (why it won't quietly break a site)

1. **Dry-run first.** `recommend_*` / `plan_*` never mutate anything. Applying is
   a separate, explicit call.
2. **Real DOM, never regex.** All edits go through BeautifulSoup + lxml, so
   markup stays well-formed.
3. **Text is preserved.** After every edit the validator re-derives the visible
   text and refuses the change if anything beyond the intended addition moved.
4. **Blast-radius caps.** Hard ceiling on edits per page (`SafetyPolicy`).
5. **Reversible.** Every `ChangeSet` carries the original HTML; `.revert()` is
   one call.
6. **No fabricated copy.** Anchors are only ever built from text already present
   on the source page.
7. **Idempotent.** Existing links are never duplicated.

If validation fails, `apply_*` returns the **original, unmodified HTML** plus the
validation errors — a failed edit is a no-op, not a broken page.

---

## Honest limitations

* **Keyword discovery is content-based**, not clickstream/volume-based. It finds
  the language competitors optimize for from their real pages; it does not pull
  search volume or ranking positions (that needs a paid SERP/keyword API). The
  `KeywordGap.gap` score is the natural hook to multiply by volume if you add one.
* **Alt text is context-derived**, not vision-derived. Without an image model we
  cannot *see* the picture, so drafts come from filename, captions, nearby
  headings and page context, and each carries a `confidence`. The audit side
  (flagging missing/stuffed/filename/too-long alts) is fully reliable; treat
  generated drafts as high-quality starting points for review, especially at low
  confidence.
* **"Cannot do any blunder"** is enforced as *strong, layered guardrails plus a
  test suite*, not a mathematical impossibility proof. The design makes silent
  content loss and malformed markup fail closed (revert to original), which is
  the practical form of that guarantee.

## Tests

```bash
cd engine && pytest -q
```
