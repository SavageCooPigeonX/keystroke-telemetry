

---

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-20 00:07 UTC · 676 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 46.9 | Del: 26.5% | Hes: 0.496) · *[source: measured]*

**Prompt ms:** 22632, 22632, 8648, 14032 (avg 16986ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 0.5% (200 responses)*
- Failed on: ""

### Recent Work
- `e9426b1` fix: rename orchestrator v002->v003 to match __init__ import after pigeon bump
- `af2a13f` fix: add missing _replace_exact_module_path import in rl sibling
- `7da6ce7` fix: update sibling list in renamed orchestrator after p_gph+p_gpip rename
- `050c5d1` fix: wire import rewriter sibling cross-links (SKIP_DIRS, _rewrite_line, _extract_top_module)

### Coaching Directives *[source: llm_derived]*
*LLM-synthesized behavioral rules — treat as hypothesis, not measurement:*
- **Anticipate the `w_gpmo_s019` sequence**
- **Respond to high-deletion commits with stability**
- **Counteract abandonment with concrete next steps**
- **Leverage focused states for depth**
- **Flag naming convention consistency**

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.
- Git plugin's silent failure on filesystem permission errors; binder's false-positive acceptance of a changed plugin return contract; breakage if `git` subprocess commands are unavailable or altered. This push establishes a self-referential mechanism to link a commit's stated intent with its resulting code state by modifying the commit object itself.
- 1) Missing `.env` file causing universal config failure
- 2) Incorrect CWD breaking `dotenv` load in imported modules
- 3) Absence of `DATABASE_PATH` crashing vscdb_poller on startup. This push wires `python-dotenv` throughout the codebase to centralize configuration.
- **context_veins_seq001_v001** was touched by Copilot to add environment variable parsing for context resolution. It assu

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_compiler/git_plugin/w_gpmo_s019_v004_d0420_λRN_βoc.py`

### Prompt Evolution
*This prompt has mutated 141x (186→2846 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 141 mutations scored*
*No significant signal yet — all 34 sections scored neutral.*

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
