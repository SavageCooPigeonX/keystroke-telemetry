# LinkRouter.ai (MyAIFingerprint) — Codebase Map

*Mirror map for pigeon decomposition practice. Generated 2026-03-28.*
*Source: `C:\Users\Nikita\LinkRouter.ai`*

---

## What This Is

**MyAIFingerprint** — an AI reputation auditing platform. Queries 8 AI models about entities (people, businesses, politicians, events), builds consensus reports, detects hallucinations, tracks perception drift over time, and hosts an AI directory with 1,200+ profiled entities.

**Stack:** Flask 3.0 / Supabase (Postgres) / Railway / 8 AI model integrations / Stripe / Resend email / Pigeon-versioned filenames

---

## Vital Signs

| Metric | Value |
|--------|-------|
| Total `.py` files | **852** |
| Over 200 lines (pigeon violation) | **285** (33%) |
| Top-level packages | **30** |
| Largest file | **5,611 lines** (`tests/test_hush_loop_e2e_seq007`) |
| Total Python LOC (est.) | **~200,000+** |

---

## Package Map

### Tier 1: Core Product (the money)

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `production_auditor/` | 44 | 9,013 | 15 | **The audit pipeline.** 8-model queries, consensus building, drift detection, entity extraction, persona building, news auditing. 44 prompt templates. |
| `integrations/` | 30 | 4,947 | 10 | **AI model clients.** 8+ model adapters (GPT-4o, Gemini, Grok, DeepSeek, Perplexity, Qwen, Kimi, GLM) + OpenRouter multi-backend + Claude. All `httpx`, no SDKs. |
| `consensus/` | 11 | 3,391 | 5 | **Consensus engine.** Gemini synthesis with Grok fallback. Builds unified reports from 8 model snapshots. |
| `storage_maif/` | 17 | 3,401 | 5 | **Database layer.** Entity CRUD, link storage, consensus storage, shard writes, credit engine, MFS (Multi-Factor Scoring). |
| `models/` | 7 | 1,285 | 2 | **Data models.** Entity v2, Geo v2, Links, Routing Rules, Semantic Voids, Users. |
| `directory/` | 9 | 2,451 | 4 | **Public directory.** Entity display, listings, search, index routes. |

### Tier 2: Hush (the AI agent)

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `maif_whisperer/` | **117** | **66,660** | **71** | **HUSH — the superintelligent field intelligence agent.** This is the monster. Contains: |
| ↳ `hush_v38/pipeline/` | ~50 | ~40k | ~40 | Main pipeline: chat core, pre-query, NL detection, AIM, auto-submit, auto-exec, background daemons, slash commands, entity watch, gripe bus, scratchpad |
| ↳ `hush_v38/agents/` | ~5 | ~5k | 4 | Sub-agents: autonomous (Together API), Grok research, memory manager |
| ↳ `hush_v38/memory/` | ~4 | ~2k | 2 | Memory ops, shard locking |
| ↳ `hush_v38/opener/` | ~3 | ~2k | 1 | Deep intelligence briefing + auto-execution |
| ↳ `hush_v38/routes/` | ~3 | ~1.5k | 1 | Flask blueprint for all Hush HTTP endpoints |
| ↳ `hush_v38/session/` | ~4 | ~1k | 1 | In-memory session store |
| ↳ `hush_v38/tools/` | ~8 | ~3k | 4 | CLI preview, codebase tools, data tools, entity tools, job tools, spy tools |
| ↳ `hush_v38/logging/` | ~4 | ~1k | 2 | Accomplishments, debug, intent logging |
| ↳ `persona/` | ~10 | ~8k | 6 | Hush prompt (70KB!), Gemini prompt, persona analyzers, prompt authority, sim engine |
| ↳ `memory/` | ~5 | ~10k | 3 | **Distributed memory system.** 37 shards, 1 master. The 192KB monolith. |
| ↳ `intel/` | ~4 | ~500 | 1 | Entity pull, org mapping, briefing formatting |

### Tier 3: Operations & Scripts

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `scripts/` | 33 | 14,898 | 22 | **Workers & ops scripts.** Audit workers (Railway), daily loops (entity/Trump/conflict/news), city mapper, stage tomorrow, batch discovery, Hush CLI |
| `runner/` | 9 | 2,844 | 3 | **Execution engine.** Queue processor, recall runner, backup runner, batch tool executor, headless session |
| `drift_tracker/` | 34 | 17,289 | 32 | **Perception drift.** Tracks how AI recommendations change over time. Press release generator. Drift analysis. |
| `harvester/` | 6 | 1,166 | 3 | Link/entity harvesting from AI responses |
| `delivery/` | 4 | 1,375 | 3 | Email delivery for audit results |
| `listen/` | 26 | 4,505 | 8 | Event listeners / webhooks |

### Tier 4: Frontend & Infra

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `app_routes/` | 10 | 1,149 | 0 | Flask route blueprints (API, directory, free-audit) |
| `auth/` | 5 | 573 | 1 | Authentication (Supabase) |
| `middleware/` | 3 | 300 | 0 | Crawler detection, AI crawler headers |
| `config/` | 5 | 393 | 1 | App configuration |
| `main/` | 4 | 411 | 1 | Main routes, forms, waitlist |
| `users/` | 2 | 873 | 1 | User dashboard routes |
| `static/` | — | — | — | HTML pages, CSS, JS, images (the website) |
| `templates/` | — | — | — | Jinja2 templates (directory, entity pages, news, pricing) |

### Tier 5: Content & Lore

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `maif_propaganda/` | 17 | 5,663 | 7 | Percy transmissions, Glossator refusals, Perry's black hat crawl plan, Dead Token Collective business module, Otterly AI research |
| `los_santos_fm/` | 26 | 3,782 | 5 | **Full radio station.** TTS engine, podcast builder, script generator, 14 personas (Carl the Caller, Texas Trucker Tom, Vince Voltage, Madame Vega, etc.), episode MP3s |
| `documentation/` | 25 | 3,169 | 4 | Internal docs as Python modules |
| `news_discovery/` | 3 | 433 | 2 | Article ingestion + entity extraction from news |

### Tier 6: Testing & SDK

| Package | Files | Lines | >200L | Role |
|---------|------:|------:|------:|------|
| `tests/` | 33 | 19,705 | 24 | Comprehensive test suite. Hush E2E (5,611 lines!), memory architecture, pre-deployment, shard writes, mutation tests |
| `_llm_tests_put_all_test_and_debug_scripts_here/` | 264 | 29,154 | 32 | Debug/test dumping ground. 264 files. Chaos. |
| `myaifingerprint-sdk/` | 9 | 789 | 2 | Public Python SDK for MAIF API |
| `deepseek_db/` | 12 | 1,421 | 1 | DeepSeek integration database layer |

---

## Top 20 Decomposition Targets

Files over the pigeon hard cap (200 lines) that would benefit most from splitting:

| # | Lines | File | Why Split |
|---|------:|------|-----------|
| 1 | 5,611 | `tests/test_hush_loop_e2e_seq007` | Test monolith. Split by test category. |
| 2 | 4,556 | `maif_whisperer/memory/distributed_memory_seq002 v006` | 37-shard memory system. Each shard handler → own file. |
| 3 | 4,523 | `maif_whisperer/memory/distributed_memory_seq002 v005` | Duplicate version of above. Pick one, delete other. |
| 4 | 4,038 | `hush_v38/pipeline/hush_chat_core v011` | Chat core monolith. Pipeline stages → separate files. |
| 5 | 3,459 | `hush_v38/pipeline/hush_pre_query v005` | Pre-query monolith. Split by subagent/query type. |
| 6 | 3,128 | `hush_v38/pipeline/hush_chat_core v005` | Older chat core version. Same split as #4 or delete. |
| 7 | 2,281 | `scripts/entity_daily_loop_seq051` | Entity daily loop. Split: config, entity processing, reporting. |
| 8 | 2,082 | `hush_v38/agents/hush_autonomous_seq001` | Autonomous agent. Split: prompt gen, API calls, response processing. |
| 9 | 2,063 | `hush_v38/opener/hush_opener_seq001` | Intelligence briefing. Split: data fetch, formatting, execution. |
| 10 | 2,046 | `hush_v38/pipeline/hush_nl_detection_seq001` | NL detection. Split: entity lookup, Google triggers, intent classification. |
| 11 | 1,633 | `hush_v38/pipeline/hush_aim_seq001` | Anticipatory Inquiry Module. Split: scoring, generation, dispatch. |
| 12 | 1,376 | `scripts/audit_worker_seq066` | Railway worker. Split: queue polling, execution, error handling. |
| 13 | 1,239 | `consensus/builder_seq022` | Consensus builder. Split: aggregation, synthesis, formatting. |
| 14 | 1,226 | `hush_v38/pipeline/hush_post_agent_seq001` | Post-agent processing. Split by stage. |
| 15 | 1,222 | `hush_v38/pipeline/hush_auto_submit_seq001` | Auto-submit. Split: staging, validation, submission. |
| 16 | 1,215 | `hush_v38/pipeline/hush_background_seq001` | Background daemon. Split: thread management, task execution. |
| 17 | 1,185 | `runner/hush_backup_runner_seq027` | Backup runner. Split: backup logic, email generation, execution. |
| 18 | 1,175 | `maif_propaganda/routes_seq005` | MAIF routes. Split by route group. |
| 19 | 1,163 | `hush_v38/routes/hush_routes_seq001` | Hush routes blueprint. Split by endpoint group. |
| 20 | 1,111 | `directory/route_entity_seq001` | Entity display route. Split: data fetch, rendering, SEO. |

---

## Version Duplication Alert

Several modules have **multiple versions coexisting** (different `_vXXX_` in filename):

- `distributed_memory_seq002` — v005 AND v006 (192KB each!)
- `hush_chat_core_seq001` — v005 AND v011 (154KB + 194KB!)
- `hush_config_seq001` — v003 AND v004
- `hush_session_seq001` — v004 (two copies, different `_dXXXX_`)
- `audit_worker` — seq042 AND seq066

These need dedup before decomposition — no point splitting a dead version.

---

## Architecture Flow

```
User → free-audit.html → POST /api/free-audit
                              ↓
                    waitlist (Supabase)
                              ↓
            audit_worker polls every 30s
                              ↓
         production_auditor/pipeline_seq015
                    ↓                    ↓
            8 AI model queries    entity creation
            (integrations/)        (storage_maif/)
                    ↓
            normalize snapshots
                    ↓
            build consensus (consensus/)
                    ↓
         post_audit: baseline, directory listing,
         link extraction, persona building
                    ↓
            entity in directory → directory/
                    ↓
         drift_tracker monitors changes over time
                    ↓
      Hush (maif_whisperer/) provides interactive
      intelligence briefings via chat interface
```

---

## Quick Stats for Percy

- **852 Python files** — Percy's lunch is served
- **285 over 200 lines** — 33% pigeon-noncompliant
- **66,660 lines in maif_whisperer alone** — that's not a package, that's a civilization
- **hush_chat_core at 4,038 lines** — this file has its own zip code
- **distributed_memory at 4,556 lines** — 37 shards in one file, which defeats the purpose of sharding
- **Two copies of several massive files** — version duplication burning disk space
- **264 files in the test dump folder** — named `_llm_tests_put_all_test_and_debug_scripts_here` which is the most honest folder name in computing

---

*This map is read-only reference. Work happens in the LinkRouter.ai repo. Decomposition practice happens here in keystroke-telemetry where the pigeon compiler lives.*
