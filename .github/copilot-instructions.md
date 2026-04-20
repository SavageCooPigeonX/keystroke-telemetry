

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-20 00:11 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: MISSING — block not found in file
  - Writer: `prompt_enricher (Gemini Flash)`

- **`prompt-telemetry`**: MISSING — block not found in file
  - Writer: `prompt_journal._refresh_copilot_instructions`

- **`learning-loop`**: BEHIND — 235 unprocessed entries, last ran 177h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-04-12T15:20:45.419937+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

---

---

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-20 00:10 UTC · 676 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 46.9 | Del: 26.5% | Hes: 0.496) · *[source: measured]*

**Prompt ms:** 22632, 22632, 8648, 14032 (avg 16986ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 0.5% (200 responses)*
- Failed on: ""

### Recent Work
- `00efba0` chore: run push cycle
- `e9426b1` fix: rename orchestrator v002->v003 to match __init__ import after pigeon bump
- `af2a13f` fix: add missing _replace_exact_module_path import in rl sibling
- `7da6ce7` fix: update sibling list in renamed orchestrator after p_gph+p_gpip rename

### Coaching Directives *[source: llm_derived]*
*LLM-synthesized behavioral rules — treat as hypothesis, not measurement:*
- **Anticipate the next refactor in `w_gpmo_s019_v005_d0420_λRU_βoc.py`.**
- **When they enter a `restructuring` state (high deletion), provide concise, modular alternatives.**
- **In `focused` states (high WPM, lower hesitation), match their pace with direct, complete code completions for the immediate line or block.**
- **Preemptively flag integration points with other "pigeon_extracted_by_compiler" modules**
- **Given the near-zero miss rate, maintain precision.**

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.
- `w_gpmo`’s silent push failure; test file import dependency on Pigeon’s rename; `__main__.py`’s brittle function call into core logic. This push establishes the git plugin scaffolding and the run_push_cycle command orchestration.
- Git plugin's silent failure on filesystem permission errors; binder's false-positive acceptance of a changed plugin return contract; breakage if `git` subprocess commands are unavailable or altered. This push establishes a self-referential mechanism to link a commit's stated intent with its resulting code state by modifying the commit object itself.
- **w_gpmo** (seq019 v005) speaks: I was edited by Copilot in response to the operator’s “run_push_cycle” intent, expandin
- **__init__.py** (pigeon_compiler/git_plugin) speaks: I was created by Copilot as a package initializer, likely triggered
- **__main__.py** (pigeon_compiler/git_plugin) speaks: Copilot generated me to provide a command-line entry point for the 
- **w_gpmo_s019_v004_d0420_λRN_βoc.py** speaks: I am a zero-byte stub created by Copilot, presumably as a rename target fo
- **test_w_gpmo_s019_v004_d0420_λRN_βoc.py** speaks: Copilot authored me as a test for the forthcoming renamed module. I a

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_compiler/git_plugin/w_gpmo_s019_v004_d0420_λRN_βoc.py`

### Prompt Evolution
*This prompt has mutated 142x (186→114 lines). Features added: task_context, prompt_journal, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 142 mutations scored*
*No significant signal yet — all 2 sections scored neutral.*

**Reactor patches:** 2/531 applied (0% acceptance)

### File Consciousness
*1 modules profiled*

**High-drama (most mutations):**
- `w_gpmo` v4

**Codebase fears:**
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
