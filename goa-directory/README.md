# Goa Business Directory — Redesign

A fast, framework-free redesign of the `goa.sanctify.*` business directory (Bootstrap/jQuery removed for better Core Web Vitals). All icons are served from a single inline SVG sprite (`assets/sprite.svg`, Lucide + SimpleIcons).

## What's here

| Path | Purpose |
|---|---|
| `index.html` | Homepage — hero search, category grid, featured listings, area tiles |
| `listing.html` | Business detail template (LocalBusiness + FAQ schema, reviews, contact rail) |
| `category.html` | Category / area landing template (ItemList + Breadcrumb schema) |
| `404.html` | Branded not-found page |
| `assets/style.css` | Design system (tokens, layout, components) |
| `assets/sprite.svg` | 34-symbol SVG icon sprite |
| `.htaccess` | HTTPS + www force, clean URLs, gzip, caching, security headers |
| `robots.txt`, `sitemap.xml` | Crawl + indexation |
| `deploy/htaccess.secondary-301.txt` | 301-redirect config for the 4 secondary subdomains (consolidation) |
| `SEO-STRATEGY.md` | Full SEO + content playbook (subdomain strategy, keywords, rollout) |

> These files use **root-relative** asset paths (`/assets/...`), which is correct for a root domain like `goa.sanctify.in`. A relative-path copy for the GitHub Pages preview lives in `/docs`.

## Deploy to production (goa.sanctify.in)

1. Upload the contents of this folder to the site's web root (`public_html` / `htdocs`).
2. Confirm `.htaccess` uploaded (it's a hidden file).
3. On the 4 secondary subdomains, rename `deploy/htaccess.secondary-301.txt` to `.htaccess` and upload it to consolidate authority (see `SEO-STRATEGY.md` §0).

## Live preview (GitHub Pages)

The `/docs` folder is a flat, relative-path build for GitHub Pages. In the repo:
**Settings → Pages → Source: this branch, folder `/docs`** → preview at `https://consecrating.github.io/goaaiseo/`.
