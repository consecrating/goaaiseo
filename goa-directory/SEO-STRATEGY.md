# Goa Business Directory — SEO & Content Strategy

A practical playbook to rank `goa.sanctify.*` on Google's first page. Read top to bottom; it goes from the biggest lever to the smallest.

---

## 0. The single most important decision: your 5 subdomains

You own **5 subdomains** serving the same directory:
`goa.sanctify.in`, `goa.sanctify.biz`, `goa.sanctify.info`, `goa.sanctify.co.in`, `goa.sanctify.co`.

If all 5 show the same listings, Google sees **duplicate content**: it picks one, ignores the other four, and may distrust all of them. Five weak clones will **never** outrank one strong site.

### ✅ Recommended: Option A — Consolidate
1. Pick **one primary domain → `goa.sanctify.in`** (`.in` performs best for India).
2. On the other 4 domains, deploy `deploy/htaccess.secondary-301.txt` (renamed `.htaccess`) to **301-redirect everything** to `goa.sanctify.in`.
3. All 13 years of authority + backlinks merge into one domain that can actually rank.
4. In Google Search Console: keep all 5 properties, watch the redirects register, submit the primary sitemap.

### Option B — Differentiate (only if you insist on keeping all 5)
Give each subdomain a **distinct purpose** with unique content, each self-canonical:
| Domain | Purpose |
|---|---|
| goa.sanctify.**in** | Main business directory (all listings) |
| goa.sanctify.**co.in** | Area guides — "Businesses in Vasco/Margao/Panaji" |
| goa.sanctify.**biz** | B2B / professional services only |
| goa.sanctify.**info** | Goa info + blog (guides, events, "best of") |
| goa.sanctify.**co** | Deals / offers, or one vertical (e.g. hospitality) |

> This is the biggest ranking lever you have. Decide this first.

---

## 1. Fix the technical foundation (already done in the rebuild)

These are corrected in the new templates — apply them site-wide:
- `lang="en-IN"` (was `zxx`).
- One **valid** JSON-LD block per page (was broken/concatenated).
- **Removed the fake `AggregateRating 4.8/4046`** on the homepage (spam-penalty risk). Only use ratings from real, verifiable reviews on individual listings.
- **Self-referencing `<link rel="canonical">`** on every page.
- Consistent Open Graph/Twitter tags pointing to the same domain.
- One Google Analytics ID across all pages.
- HTTPS + www forced, clean URLs, gzip, caching, security headers (`.htaccess`).
- Fast, framework-free front-end → better Core Web Vitals (a ranking factor).

---

## 2. Content architecture — the pages that rank

Directories rank through **"category × area" long-tail pages**. Build this tree:

```
Home
├─ /categories/{category}                 e.g. /categories/spa-salon-goa
│    └─ /categories/{category}/{subcat}    e.g. .../beauty-parlours-in-goa
├─ /areas/{area}                           e.g. /areas/vasco   (NEW — high value)
│    └─ /areas/{area}/{category}           e.g. /areas/vasco/salons  (best of both)
├─ /listings/{business-slug}               the money pages
└─ /blog/{article}                         traffic magnets that link inward
```

**Priority order to build:**
1. Category pages (you have the URLs already).
2. **Area landing pages** (`/areas/vasco`, `/margao`, `/panaji`, `/candolim`, `/calangute`, `/dabolim`) — these capture "in Vasco / near me" searches and barely any competitor does them well.
3. Rich listing pages.
4. Blog guides.

---

## 3. Keyword map (Goa local intent)

Target **long-tail, high-intent** phrases, not generic heads.

| Page | Primary keyword | Supporting keywords |
|---|---|---|
| Home | goa business directory | local businesses in goa, goa classifieds |
| Category | best spa & salons in goa | beauty parlour in goa, hair salon goa |
| Category×Area | beauty parlour in vasco | salon in vasco goa, bridal makeup vasco |
| Area | businesses in margao | shops & services in margao goa |
| Listing | {business name} vasco goa | {service} in {area}, {name} contact number |
| Blog | best restaurants in north goa | where to eat in goa, goa cafe guide |

**How to find more:** Google autocomplete + "People also ask" + the "Searches related to…" footer for each seed term. Free and Goa-specific.

---

## 4. On-page content templates

### 4a. Listing page (aim 300–500+ unique words)
- `H1` = Business name + area (e.g. "Ria's Beauty Parlour, Vasco").
- 2–3 paragraphs: what they do, who they serve, what makes them good (write **unique** copy — never paste the same blurb across sites).
- Services list (bullets or chips).
- NAP: Name, Address, Phone — **identical everywhere** (site, GBP, Facebook).
- Hours, map embed, 3–5 real photos (compressed, descriptive `alt` text).
- Real reviews + a "Write a review" link.
- FAQ (3+ Q&As) with `FAQPage` schema.
- Valid `LocalBusiness` schema (see `listing.html`).

### 4b. Category / Area page
- `H1` with the exact keyword ("Best Spa & Salons in Goa").
- 150–250 word **intro** answering searcher intent (see `category.html`).
- Filterable list of listings (area, sub-category, rating).
- Internal links to related categories/areas.
- FAQ block + `ItemList` + `BreadcrumbList` schema.

### 4c. Blog article
- Answer a real question ("Top 10 restaurants in North Goa 2026").
- 800–1500 words, headings, images, and **internal links to your listings** — this funnels authority to money pages.

---

## 5. Off-page & local SEO (this is where rankings are won)

1. **Google Business Profile** for the directory itself + help each listed business claim theirs.
2. **NAP consistency** across the web (same name/address/phone format everywhere).
3. **Local citations** — list the directory in JustDial, Sulekha, IndiaMART, other Goa directories.
4. **Backlinks** — reach out to Goa blogs, tourism sites, local news, business associations. Even 10–20 quality local links move the needle.
5. **Reviews** — encourage listed businesses to gather Google reviews; embed genuine ones.
6. **Social signals** — post listings/guides on the existing Facebook/Instagram/YouTube.

---

## 6. Get more listings (non-negotiable)

A directory with ~12 businesses cannot rank. **Target 100+ real listings.**
- Run an "add your business free" drive across Goa.
- Seed categories that are empty (most show `00`).
- Each new unique listing = a new indexable, rankable page.

---

## 7. 90-day rollout

**Weeks 1–2 — Foundation**
- Decide subdomain strategy (Section 0) and deploy redirects if consolidating.
- Push the new design live; verify Search Console + Analytics; submit sitemap.

**Weeks 3–6 — Content build-out**
- Rewrite/expand all category pages with intro copy + FAQ + schema.
- Launch 6 area landing pages.
- Rewrite existing listings to 300+ unique words each.

**Weeks 7–12 — Growth**
- Add 50–100 new listings.
- Publish 4–6 blog guides, each linking to listings.
- Start citations + local backlink outreach; push for Google reviews.

**Ongoing** — track keyword rankings, fix Search Console coverage errors, add listings weekly.

---

## 8. Measuring success
- **Google Search Console**: impressions, clicks, avg position, coverage.
- **GA4**: organic sessions, top landing pages, calls/WhatsApp clicks (set as conversions).
- **Rank tracking**: a handful of target "category in area" keywords.

> North star: move from "indexed but invisible" to page-1 for **"[category] in [area] goa"** long-tails — that's where ready-to-buy local searchers are.
