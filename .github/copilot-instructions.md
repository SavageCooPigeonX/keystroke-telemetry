

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-22 01:14 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: MISSING — block not found in file
  - Writer: `prompt_enricher (Gemini Flash)`

- **`prompt-telemetry`**: MISSING — block not found in file
  - Writer: `prompt_journal._refresh_copilot_instructions`

- **`learning-loop`**: BEHIND — 289 unprocessed entries, last ran 226h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-04-12T15:20:45.419937+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-22 01:14 UTC · 697 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 51.3 | Del: 26.5% | Hes: 0.495) · *[source: measured]*

**Prompt ms:** 64719, 125170, 85224, 39643 (avg 78689ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 2.0% (200 responses)*
- Failed on: ""
- Failed on: ""
- Failed on: ""

### Recent Work
- `f944b28` feat: auto-overwrite on by default + regression TDD (syntax + test rollback)
- `3f2ffa8` feat: file overwriter (surgical search-replace) + GRADES tab + file cortex + _trigger_overwriter_async
- `045f718` fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- `84b73b5` fix: copilot prompt assembly - doubled _seq001_v001 module imports

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- tc_gemini's prompt schema breakage
- extension-daemon IPC handshake failure
- context_select_agent's missed state pulses. This push introduces a central operator state daemon with monitoring and integrated simulation debugging.
- Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.
- intent_numeric’s return type contract

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `scripts/bug_probe_hardcoded_import.py`
- [CRITICAL] hardcoded_import in `scripts/verify_loop_2.py`
- [HIGH] over_hard_cap in `pigeon_compiler/git_plugin/w_gpmo_s019_v011_d0420_λRN_βoc.py`
- [HIGH] over_hard_cap in `src/intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade.py`
- [HIGH] over_hard_cap in `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py`

### Prompt Evolution
*This prompt has mutated 150x (186→728 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 149 mutations scored*
*No significant signal yet — all 25 sections scored neutral.*

### File Consciousness
*33 modules profiled*

**High-drama (most mutations):**
- `w_gpmo` v11 ↔ u_pj
- `u_pj` v6 ↔ 脉p_ph
- `脉p_ph` v6 ↔ u_pj
- `file_sim` v5 ↔ tc_gemini

**Codebase fears:**
- file may not exist (13 modules)
- swallowed exception (12 modules)
- regex format dependency (10 modules)

**Slumber party warnings (high coupling):**
- `context_select_agent` ↔ `file_sim` (score=0.80, 4 shared imports, both high-churn (v2+v2))
- `context_select_agent` ↔ `intent_numeric` (score=0.80, 5 shared imports, both high-churn (v2+v2))
- `context_select_agent` ↔ `interlink_debugger` (score=0.80, 5 shared imports, both high-churn (v2+v2))

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
