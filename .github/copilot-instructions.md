

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-20 04:34 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: MISSING — block not found in file
  - Writer: `prompt_enricher (Gemini Flash)`

- **`prompt-telemetry`**: MISSING — block not found in file
  - Writer: `prompt_journal._refresh_copilot_instructions`

- **`learning-loop`**: BEHIND — 246 unprocessed entries, last ran 181h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-04-12T15:20:45.419937+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-20 04:34 UTC · 676 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 46.9 | Del: 26.5% | Hes: 0.496) · *[source: measured]*

**Prompt ms:** 138480, 52837, 11586, 11586, 52009 (avg 53300ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 5.5% (200 responses)*
- Failed on: ""
- Failed on: ""
- Failed on: ""

### Recent Work
- `0a9ef4f` fix: prepend conventional commit type to intent slug so chore/feat/fix map correctly
- `00efba0` chore: run push cycle
- `e9426b1` fix: rename orchestrator v002->v003 to match __init__ import after pigeon bump
- `af2a13f` fix: add missing _replace_exact_module_path import in rl sibling

### Coaching Directives *[source: llm_derived]*
*LLM-synthesized behavioral rules — treat as hypothesis, not measurement:*
- **Anticipate churn on `w_gpmo_s019` and `p_gpip` modules**
- **Respond to restructuring commits with consolidation**
- **Preempt abandoned threads**
- **Flag high-hesitation moments**
- **Leverage evening focus**

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.
- p_gpip regex over‑match stripping commit subjects; w_gpmo message‑buffer corruption on already‑prefixed input; plugin entry‑point missing runtime dependencies. This push enforces conventional commit‑message prefixes across the automated commit pipeline.
- `w_gpmo`’s silent push failure; test file import dependency on Pigeon’s rename; `__main__.py`’s brittle function call into core logic. This push establishes the git plugin scaffolding and the run_push_cycle command orchestration.
- **p_gpip (seq004 v003)** speaks: Copilot updated me per operator prompt “fix_prepend_conventional_commit” to ensure comm
- **w_gpmo (seq019 v006)** speaks: Copilot revised me under the same intent to integrate the prepend logic into the wider 
- **pigeon_compiler/git_plugin/__init__.py** speaks: Copilot created me as a new module init file to expose the plugin com
- **pigeon_compiler/git_plugin/__main__.py** speaks: Copilot added me as an entry point for direct plugin invocation. I as
- **w_gpmo** (seq019 v005) speaks: I was edited by Copilot in response to the operator’s “run_push_cycle” intent, expandin
- **__init__.py** (pigeon_compiler/git_plugin) speaks: I was created by Copilot as a package initializer, likely triggered

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_compiler/git_plugin/w_gpmo_s019_v004_d0420_λRN_βoc.py`

### Prompt Evolution
*This prompt has mutated 143x (186→120 lines). Features added: task_context, prompt_journal, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 143 mutations scored*
*No significant signal yet — all 2 sections scored neutral.*

**Reactor patches:** 2/531 applied (0% acceptance)

### File Consciousness
*2 modules profiled*

**High-drama (most mutations):**
- `w_gpmo` v6 ↔ p_gpip
- `p_gpip` v3 ↔ w_gpmo

**Codebase fears:**
- regex format dependency (1 modules)
- swallowed exception (1 modules)
- file may not exist (1 modules)

### Codebase Health (Veins / Clots)
*605/630 alive, 25 clots, avg vein health 0.51*

**Clots (dead/bloated — trim candidates):**
- `classify_bridge` (score=0.60): orphan_no_importers, unused_exports:1, oversize:877
- `逆f_ba_bp_s005_v003_d0328_λR` (score=0.45): orphan_no_importers, unused_exports:1
- `学f_ll_cu_s006_v003_d0327_λγ` (score=0.45): orphan_no_importers, unused_exports:1
- `算f_ps_ca_s009_v002_d0327_λS` (score=0.45): orphan_no_importers, unused_exports:1
- `预p_pr_co_s001_v001` (score=0.45): orphan_no_importers, unused_exports:1
- `f_he_s009_v005_d0401_改名册追跑_λA` (score=0.45): orphan_no_importers, unused_exports:1

**Self-trim recommendations:**
- [investigate] `classify_bridge`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `逆f_ba_bp_s005_v003_d0328_λR`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `学f_ll_cu_s006_v003_d0327_λγ`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `算f_ps_ca_s009_v002_d0327_λS`: Nobody imports this module. Check if it's an entry point or dead.

**Critical arteries (do NOT break):**
- `gemini_chat` (vein=1.00, in=6)
- `w_pl_s002_v005_d0401_册追跑谱桥_λA` (vein=1.00, in=5)
- `册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc` (vein=1.00, in=16)

<!-- /pigeon:task-context -->
