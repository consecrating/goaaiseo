# GOAAISEO — The Autonomous SEO Operating System

> An AI-native SEO Operating System that fuses Search Console intelligence, crawling,
> topical authority modeling, AI-search optimization, local SEO, and autonomous
> agents into a single closed-loop platform built for agencies, local businesses,
> and AI-search-first content teams.

GOAAISEO is **not** a keyword tracker with a dashboard. It is a system that:

1. **Ingests** ground-truth performance data (Google Search Console, GA4) instead of guessing from third-party clickstream models.
2. **Crawls** and structurally models your site as a graph (pages, links, entities, clusters).
3. **Reasons** over that graph with LLMs + retrieval to find opportunities humans miss.
4. **Acts** — drafts schema, internal links, content briefs, and pushes them to WordPress.
5. **Closes the loop** — measures the impact of each action against GSC ground truth and learns.

---

## Blueprint Index

This repository contains the complete technical blueprint. Read in order, or jump to a phase.

| Phase | Document | Focus |
|------|----------|-------|
| 1 | [First-Principles Analysis](docs/blueprint/01-first-principles.md) | Capabilities, tool benchmark, weaknesses, AI opportunities, moat |
| 2 | [System Architecture](docs/blueprint/02-system-architecture.md) | Stack, rationale, Mermaid diagrams |
| 3 | [SEO Crawler Engine](docs/blueprint/03-crawler-engine.md) | Schema, API, workflows |
| 4 | [Search Console Intelligence](docs/blueprint/04-search-console-intelligence.md) | Pipeline, scoring models |
| 5 | [Topical Authority Engine](docs/blueprint/05-topical-authority-engine.md) | Clustering algorithms, pseudocode |
| 6 | [AI Search Optimization](docs/blueprint/06-ai-search-optimization.md) | GEO/AEO scoring framework |
| 7 | [Local SEO Engine](docs/blueprint/07-local-seo-engine.md) | GBP, NAP, citations workflow |
| 8 | [Competitor Intelligence](docs/blueprint/08-competitor-intelligence.md) | Change-detection monitoring |
| 9 | [Internal Linking AI](docs/blueprint/09-internal-linking-ai.md) | Link-equity algorithm |
| 10 | [WordPress Integration](docs/blueprint/10-wordpress-integration.md) | Plugin architecture |
| 11 | [Autonomous SEO Agent](docs/blueprint/11-autonomous-agent.md) | Agent / prompt / memory |
| 12 | [Repository Structure](docs/blueprint/12-repository-structure.md) | Production monorepo layout |
| 13 | [Implementation Roadmap](docs/blueprint/13-implementation-roadmap.md) | Phased delivery plan |
| 14 | [Analysis-Layer Adoption](docs/blueprint/14-analysis-layer-adoption.md) | Buy vs. build: adopt `claude-seo` for analysis, build the loop |

The single-file master document is [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md).

---

## The 30-Second Pitch

Traditional SEO tools (Ahrefs, Semrush) are **estimation engines** built on third-party
clickstream data and link indexes. They are excellent at competitive discovery but blind
to *your* truth and unable to *act*. Technical crawlers (Screaming Frog, Sitebulb) see
structure but not search demand. Content tools (Surfer, Clearscope, MarketMuse) optimize
single pages but ignore site-wide topical structure and ground-truth performance.

**GOAAISEO's moat** is the closed loop between four signals nobody else unifies in real time:

```
GSC ground truth  ⟷  Site graph (crawl)  ⟷  Entity/topic model  ⟷  Autonomous action
        ▲                                                                    │
        └──────────────────── measured impact feeds back ────────────────────┘
```

## Tech Stack (summary)

- **Frontend:** Next.js 15 (App Router) + React 19 + TypeScript + Tailwind + shadcn/ui + TanStack Query
- **API/Orchestration:** Node.js (NestJS) for transactional + realtime APIs
- **Data/ML services:** Python (FastAPI) for crawling, NLP, embeddings, scoring
- **Database:** PostgreSQL 16 + `pgvector` (via Supabase) + TimescaleDB for time-series GSC data
- **Queue:** Redis + BullMQ (Node) / Celery or Arq (Python) for distributed crawl & analysis jobs
- **Cache:** Redis
- **Storage:** Supabase Storage / S3-compatible (raw HTML, render snapshots, exports)
- **Auth:** Supabase Auth (OAuth + RLS) with Google OAuth for GSC/GA4 scopes
- **Infra:** Docker, GitHub Actions CI/CD, deployed to Vercel (web) + Fly.io/Railway/AWS ECS (services)

See [Phase 2](docs/blueprint/02-system-architecture.md) for the full rationale.

## Status

This is a **blueprint / architecture** repository. Code skeletons under `apps/` and
`services/` illustrate the intended structure described in
[Phase 12](docs/blueprint/12-repository-structure.md).

## License

Proprietary — internal blueprint. Add a license before public release.
