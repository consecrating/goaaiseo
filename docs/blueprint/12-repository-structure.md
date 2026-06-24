# Phase 12 — Production Repository Structure

> A polyglot monorepo (Turborepo + pnpm workspaces for JS, uv workspaces for Python) that
> mirrors the architecture in Phase 2: a Next.js web app, a NestJS API, several Python services,
> shared packages, the WordPress plugin, infra, and docs — all CI/CD-ready.

---

## 12.1 Top-level layout

```
goaaiseo/
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── .env.example
├── turbo.json                      # Turborepo pipeline (build/lint/test/dev)
├── pnpm-workspace.yaml             # JS workspaces
├── package.json                    # root scripts + devDeps
├── pyproject.toml                  # uv workspace root for Python services
├── docker-compose.yml              # local dev: postgres, redis, services
├── Makefile                        # one-liners: make dev / make test / make migrate
│
├── apps/                           # deployable applications
│   ├── web/                        # Next.js 15 frontend
│   ├── api/                        # NestJS transactional/realtime API
│   └── docs-site/                  # (optional) Docusaurus/Nextra for public docs
│
├── services/                       # Python ML/data services (FastAPI + workers)
│   ├── crawler/
│   ├── nlp/
│   ├── scoring/
│   ├── geo-probe/
│   └── connectors/                 # GSC / GA4 / GBP / SERP ingestion
│
├── packages/                       # shared JS/TS libraries
│   ├── contracts/                  # zod/ts types shared web↔api (and OpenAPI gen)
│   ├── ui/                         # shadcn/ui component library
│   ├── config/                     # eslint, tsconfig, tailwind presets
│   └── sdk/                        # typed client for the public API
│
├── py-packages/                    # shared Python libraries
│   ├── goaaiseo_core/              # domain models, scoring math, graph utils
│   └── goaaiseo_db/                # SQLAlchemy models, query helpers
│
├── wordpress/
│   └── goaaiseo-wp/                # the plugin (see Phase 10 for internal layout)
│
├── db/
│   ├── migrations/                 # SQL migrations (Sqitch/Atlas/Prisma-migrate)
│   ├── schema.sql                  # full canonical schema (all phases combined)
│   └── seed/                       # seed + fixture data
│
├── infra/
│   ├── docker/                     # per-service Dockerfiles
│   ├── terraform/                  # cloud infra as code (DB, Redis, storage, DNS)
│   ├── k8s/ or fly/                # deploy manifests
│   └── observability/              # otel collector, dashboards, alert rules
│
├── .github/
│   └── workflows/                  # CI/CD pipelines (see 12.5)
│
└── docs/
    ├── BLUEPRINT.md                # single-file master blueprint
    ├── blueprint/                  # phase-by-phase docs (this directory)
    ├── adr/                        # architecture decision records
    └── api/                        # generated OpenAPI specs
```

---

## 12.2 `apps/web` (Next.js 15)

```
apps/web/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── app/
│   ├── (auth)/login/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── overview/page.tsx
│   │   ├── opportunities/page.tsx        # unified backlog (Phase 4)
│   │   ├── crawl/[runId]/page.tsx         # crawl results + site graph (Phase 3)
│   │   ├── topics/page.tsx                # topical map (Phase 5)
│   │   ├── ai-search/page.tsx             # GEO/citations (Phase 6)
│   │   ├── local/page.tsx                 # local SEO (Phase 7)
│   │   ├── competitors/page.tsx           # change stream (Phase 8)
│   │   ├── internal-links/page.tsx        # linking AI (Phase 9)
│   │   └── agent/page.tsx                 # agent runs + reports (Phase 11)
│   └── api/                               # route handlers / server actions (BFF)
├── components/                            # feature components (charts, graph viz, tables)
├── lib/                                   # api client (uses packages/sdk), auth, query
└── hooks/
```

## 12.3 `apps/api` (NestJS)

```
apps/api/
├── package.json
├── nest-cli.json
├── src/
│   ├── main.ts
│   ├── app.module.ts
│   ├── common/            # guards (auth/RLS), interceptors, filters, pipes
│   ├── auth/              # Supabase JWT verification, org context
│   ├── orgs/ projects/ sites/                  # tenancy + config
│   ├── crawl/             # proxy + status for crawler service
│   ├── gsc/               # opportunities, reports (reads Timescale)
│   ├── topics/ ai-search/ local/ competitors/ links/   # engine read APIs
│   ├── agent/             # agent runs, actions, approvals
│   ├── queue/             # BullMQ producers (enqueue jobs to Python workers)
│   └── billing/           # plans, quotas, usage metering
└── test/
```

## 12.4 `services/*` (Python FastAPI + workers)

```
services/crawler/
├── pyproject.toml
├── Dockerfile
├── app/
│   ├── main.py            # FastAPI (health, sync queries)
│   ├── worker.py          # Arq/Celery worker entrypoint
│   ├── frontier.py fetcher.py renderer.py parser.py dedup.py
│   ├── analyze.py         # pagerank, orphans, dupes, issues (post-crawl)
│   └── tasks.py           # queue handlers: crawl.start, analyze.site
└── tests/

services/nlp/        # embeddings, entity extraction, clustering (Phase 5)
services/scoring/    # opportunity + GEO + topical scoring (Phases 4,5,6)
services/geo-probe/  # multi-engine AI probing (Phase 6)
services/connectors/ # gsc.py ga4.py gbp.py serp.py ingestion workers (Phase 4,7,8)
```

Each service shares `py-packages/goaaiseo_core` (domain math) and `py-packages/goaaiseo_db`
(SQLAlchemy models) so schemas and scoring formulas have a single source of truth.

---

## 12.5 CI/CD (`.github/workflows`)

```
.github/workflows/
├── ci.yml                 # lint + typecheck + unit tests (matrix: node, python)
├── build-images.yml       # build & push Docker images on main/tags
├── deploy-web.yml         # deploy apps/web to Vercel
├── deploy-services.yml    # deploy api + python services to Fly.io/ECS
├── db-migrate.yml         # gated migration run against staging/prod
├── wp-plugin.yml          # build + lint + package the WordPress plugin (PHPCS, zip artifact)
└── codeql.yml             # security scanning
```

`turbo.json` caches builds and runs only affected packages; `ci.yml` uses path filters so a
docs-only change (like this blueprint) doesn't trigger full service builds.

---

## 12.6 Conventions

| Concern | Convention |
|---|---|
| **Types** | `packages/contracts` (zod) is the source of truth; OpenAPI generated for Python + SDK. |
| **DB** | `db/migrations` forward-only; `db/schema.sql` is the assembled canonical schema. |
| **Env** | `.env.example` documents every var; secrets via platform secret stores, never committed. |
| **Testing** | Vitest (JS), pytest (Python), Playwright (e2e), PHPUnit (plugin). |
| **Lint/format** | ESLint+Prettier (JS), Ruff+Black (Python), PHPCS (WP), enforced in CI. |
| **ADRs** | Every significant decision recorded in `docs/adr` (e.g., "why Timescale for GSC"). |
| **Commits** | Conventional Commits; PR template requires linked issue + test evidence. |

This structure lets each piece scale and deploy independently while keeping schemas, types, and
scoring logic centralized — the discipline a production SEO Operating System needs.
