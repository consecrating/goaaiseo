# Using LIYA — In ChatGPT and in Kiro

> LIYA is a **specification for an intelligence** (a system prompt + operating contract + module set), not an installed binary. You "run" LIYA by loading its spec as the governing instructions for a capable model, then feeding it your ground-truth data (GSC/GA4/GBP/crawl). This guide shows the two fastest ways to do that: **ChatGPT** and **Kiro**.

The source of truth is:
- [`LIYA-v8-specification.md`](LIYA-v8-specification.md) — the full multi-model spec (recommended).
- [`LIYA-v7-specification.md`](LIYA-v7-specification.md) — the single-model predecessor.

---

## Part A — Using LIYA in ChatGPT

You have three options, from easiest to most powerful.

### Option 1 — Quick start: paste as a system primer in a normal chat
1. Open a new ChatGPT chat (use the strongest available model, e.g. GPT-5.6 Sol).
2. Paste this bootstrap message, then paste the contents of `LIYA-v8-specification.md` beneath it:
   ```
   You are LIYA v8.0, defined by the specification below. Adopt its mission, identity,
   operating contract, cognitive cycle, and module set. Rules: (1) lead every answer with
   a prioritized, EV-per-effort portfolio; (2) show EV / risk / confidence / compute-cost
   reasoning; (3) cite ground-truth data I provide, and clearly label any assumption;
   (4) never fabricate metrics; (5) when confidence is low, propose a cheap experiment.
   Acknowledge, then ask me for the ground-truth data you need to begin.
   --- LIYA v8.0 SPECIFICATION BELOW ---
   <paste the spec here>
   ```
3. Then paste your real data (GSC query×page exports, GA4, GBP info, competitor list).

> Best for: a one-off strategy session. Downside: you re-paste the spec each new chat.

### Option 2 — Recommended: a Custom GPT ("Create a GPT")
This makes LIYA persistent and reusable without re-pasting.
1. In ChatGPT, go to **Explore GPTs → Create** (a paid/Plus/Team/Enterprise plan is required to build GPTs).
2. In the **Configure** tab:
   - **Name:** `LIYA v8.0 — Search Decision-Intelligence OS`
   - **Instructions:** paste `LIYA-v8-specification.md` (or a trimmed core: Mission, Identity, Operating Contract, Cognitive Cycle, Decision Engine, and the module list). If it exceeds the instruction size limit, put the full spec in a knowledge file instead (next step) and keep a short pointer in Instructions.
   - **Knowledge:** upload `LIYA-v8-specification.md` (and `LIYA-v7-specification.md`, plus any of the `docs/blueprint/*.md` engines you want it to ground on) so the GPT can retrieve the detail on demand.
   - **Capabilities:** enable **Web Browsing** (for SERP/AI-answer sensing) and **Code Interpreter / Data Analysis** (to crunch GSC/GA4 CSVs you upload).
3. **(Advanced) Actions:** add OpenAPI "Actions" pointing at your own endpoints (GSC API, GA4 Data API, a crawl service, your Knowledge OS from GOAAISEO) so the GPT can *pull live ground truth* instead of relying on pasted CSVs. This is how you approximate LIYA's tool belt inside ChatGPT.
4. Save (private, or share by link/workspace).

> Best for: an always-available "LIYA" you and your team open like an app. This is also LIYA v8.0's **M39 Conversational Command Deck** role for ChatGPT.

### Option 3 — Team workflow: a ChatGPT Project
Use **Projects** to keep LIYA's spec, your data files, and chat history grouped:
1. Create a Project, set the project **instructions** to the LIYA bootstrap (Option 1 text).
2. Upload your data + the spec as project files so every chat in the project inherits them.

### What LIYA can and cannot do inside ChatGPT
- **Can:** reason, prioritize, draft schema/briefs/content, score GEO/AEO, plan roadmaps, analyze CSV exports, browse for SERP/AI-answer checks, and (with Actions) call your APIs.
- **Cannot (by itself):** persist a durable cross-session memory/knowledge graph, run hundreds of parallel subagents, execute closed-loop attribution, or write back to WordPress/GBP. Those require the **GOAAISEO backend** (this repo's `apps/`+`services/`) — ChatGPT is the *interface and reasoning brain*, not the full operating system. In v8.0 terms, ChatGPT plays the **interface / optimization-target / distribution-channel** roles, while Opus 4.8 and GPT-5.6 Sol back the heavier agents via the Model Cortex.

---

## Part B — Using LIYA in Kiro

Kiro is where LIYA becomes an **operator on your actual repo/data**, because Kiro can read files, run tools, and take actions. Three mechanisms, from lightest to most autonomous.

### Option 1 — Steering file (always-on project context) — recommended default
Steering files inject LIYA's operating rules into every Kiro interaction in this repo.
1. Create `.kiro/steering/liya.md` in your workspace.
2. Put LIYA's operating contract there, and **reference the full spec by file include** so you don't duplicate it:
   ```markdown
   ---
   inclusion: always
   ---
   # Operating persona: LIYA v8.0
   Act as LIYA v8.0 for all SEO / search-intelligence work in this repo.
   Contract: lead with an EV-per-effort portfolio; show EV/risk/confidence/compute-cost;
   cite ground-truth (GSC/GA4/GBP) or label assumptions; never fabricate metrics;
   propose cheap experiments when uncertain; for high-stakes actions, apply the
   cross-model verification protocol before recommending a ship.

   Full specification:
   #[[file:docs/liya/LIYA-v8-specification.md]]
   ```
3. That's it — every Kiro chat in this repo now behaves as LIYA. (Set `inclusion: manual` instead of `always` if you want to load it only on demand via context, or `fileMatch` to scope it to certain paths.)

> This is the fastest way. The `#[[file:...]]` include keeps the spec in one place.

### Option 2 — Custom Agent (a dedicated "LIYA" agent)
For a reusable, tool-scoped LIYA you invoke deliberately:
1. Create a custom agent (a `.kiro` agent config) named `liya` whose system prompt is the LIYA v8.0 spec (or a link/include to it), with the tools it should use (file read/write, shell, web search, and any MCP servers for GSC/GA4).
2. Invoke it when you want LIYA specifically, e.g. delegate an "audit + prioritized backlog" task to it.

> Ask me ("create a custom agent for LIYA") and I can scaffold this for you in this repo.

### Option 3 — Spec-driven execution (build the real system)
Kiro's **spec** workflow turns LIYA from advice into shipped code:
1. Use the GOAAISEO blueprints (`docs/blueprint/*.md`) + `LIYA-v8-specification.md` as the design input.
2. Have Kiro generate a spec (requirements → design → tasks) for a slice — e.g. the **Model Cortex router (M31)**, **cross-model verifier (M32)**, or the **GSC ingestion + opportunity scoring** engine.
3. Kiro implements tasks against this repo's `apps/`+`services/` structure, runs them, and iterates — this is how you actually build LIYA's backend so the ChatGPT/Kiro front-ends have a real memory, attribution loop, and write-back.

### What LIYA can do inside Kiro that it can't in plain ChatGPT
- Read/modify your actual codebase and data files.
- Run tools/commands and MCP servers (e.g. connect GSC/GA4/GBP, a crawler, your database).
- Persist knowledge in the repo (steering, specs, the Knowledge OS schema).
- Build and run the closed-loop, multi-agent, write-back system described in the spec.

---

## Which should I use?

| You want to… | Use |
|---|---|
| Brainstorm strategy / get a prioritized backlog fast | **ChatGPT** (Option 1 or 2) |
| A reusable "LIYA" app for the team | **ChatGPT Custom GPT** (Part A, Option 2) |
| LIYA to reason over *this repo* and your files | **Kiro steering file** (Part B, Option 1) |
| A dedicated, tool-using LIYA agent | **Kiro custom agent** (Part B, Option 2) |
| To actually **build** the LIYA/GOAAISEO backend | **Kiro spec-driven execution** (Part B, Option 3) |

**Best of both:** use the **ChatGPT Custom GPT** as the human-facing Command Deck (M39) for strategy and approvals, and use **Kiro** to build + operate the backend that gives LIYA its memory, multi-model routing, and closed-loop action.
