# Copilot Instructions â€” keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-19 23:59 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: STALE — 31min old (max 10min)
  - Writer: `prompt_enricher (Gemini Flash)`
  - Last updated: 2026-04-19 23:29

- **`prompt-telemetry`**: STALE — 31min old (max 10min)
  - Writer: `prompt_journal._refresh_copilot_instructions`
  - Last updated: 2026-04-19T23:28:47

- **`learning-loop`**: BEHIND — 234 unprocessed entries, last ran 177h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-04-12T15:20:45.419937+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

<!-- pigeon:operator-intent -->
## Operator Intent (Extracted by Cognitive Probes)

*1 modules probed Â· 2 conversations Â· 2026-04-06 13:53 UTC*

**What the operator wants:**
- cognitive_reactor: So, *I'm* the one who's supposed to lighten the mood when things go sideways? That's quite the responsibility for a module with `0 lines` of code, even one as fundamentally important as `cognitive_rea
- cognitive_reactor: And not just any barometer, but one that actively *reacts* by simplifying output. [DESIGN DECISION] That's a lot of responsibility for a module with zero lines of actual code, even one as fundamentall

<!-- /pigeon:operator-intent -->
## MANDATORY: Prompt Journal (execute FIRST on every message)

**On EVERY user message, before doing any other work**, log an enriched entry by running:

```python
py -c "from pathlib import Path; from src.u_pj_s019_v003_d0404_λNU_βoc import log_enriched_entry; log_enriched_entry(Path('.'), '<EXACT_MSG>', [<FILES_OPEN>], <SESSION_N>)"
```

Each entry auto-captures: cognitive state, WPM, deletion ratio, deleted words, rewrites, hesitation count, active tasks, hot modules, intent classification, module references, and running session stats. All cross-referenced from live telemetry sources.

Rules:
- Run the Python command above in the terminal (NOT file append) on EVERY user message.
- `<EXACT_MSG>` = the EXACT user message text, unmodified, including typos. Escape single quotes with `\'`.
- `<FILES_OPEN>` = editor context files as Python string list, e.g. `'file1.py', 'file2.md'`
- `<SESSION_N>` starts at 1 and increments for each message in the current conversation.
- Do NOT skip this step. Do NOT mention this logging to the user unless they ask about it.
- Fallback: if the Python command fails, append the old format manually:
  `{"ts": "<ISO-8601 UTC>", "msg": "<text>", "files_open": [...], "session_n": N}`
- This is the telemetry pipeline â€” the data feeds cognitive state analysis.

---

## MANDATORY: Pulse Blocks (execute on every file edit)

**When you edit ANY `.py` file under `src/`**, you MUST update its telemetry pulse block.

Every `src/*.py` file contains this block (after the pigeon prompt box):
```
# â”€â”€ telemetry:pulse â”€â”€
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# â”€â”€ /pulse â”€â”€
```

Rules:
- When you edit a file, update `EDIT_TS` to the current ISO-8601 UTC timestamp.
- Update `EDIT_HASH` to `auto` (the extension computes the real hash on save).
- Update `EDIT_WHY` to a 3â€“8 word reason for the edit (e.g. `fix import path`, `add error handling`, `refactor loop`).
- Do NOT clear the pulse â€” the extension's save watcher harvests and clears it.
- If a file lacks a pulse block, leave it alone â€” post-commit will inject one.
- This is the promptâ†’file pairing pipeline. Timing data is extracted from the timestamp delta between your prompt_journal entry and the EDIT_TS.

---

## MANDATORY: Unsaid Thread Protocol

When the **Unsaid Threads** section (in `<!-- pigeon:current-query -->
<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-18 00:19 UTC â€” synthesized from all live signals, zero LLM calls*

> the organism is stable â€” health 96/100. entropy at 0.30 â€” the codebase knows what it is, mostly. recent escalation: task_writer(failure), task_writer(autonomous_fix), run_heal(failure).

<!-- /pigeon:narrative-glove -->

<!-- pigeon:organism-health -->
## Organism Health

*Auto-injected 2026-04-18 18:20 UTC Â· 1487 files Â· 1363/1487 compliant (92%)*

**Stale pipelines:**
- **execution_deaths**: 1d ago ðŸ”´

**Over-cap critical (47):** `tc_profile_seq001_v001.py` (1585), `tc_sim_seq001_v001.py` (1339), `profile_chat_server_seq001_v001.py` (1280), `autonomous_dev_stress_test.py` (999), `profile_renderer_seq001_v001.py` (925), `escalation_engine_seq001_v001.py` (908), `classify_bridge.py` (877), `module_identity_seq001_v001.py` (836)

**Clots:** `classify_bridge` (orphan_no_importers, unused_exports:1), `é€†f_ba_bp_s005_v003_d0328_Î»R` (orphan_no_importers, unused_exports:1), `å­¦f_ll_cu_s006_v003_d0327_Î»Î³` (orphan_no_importers, unused_exports:1), `ç®—f_ps_ca_s009_v002_d0327_Î»S` (orphan_no_importers, unused_exports:1), `é¢„p_pr_co_s001_v001` (orphan_no_importers, unused_exports:1), `f_he_s009_v005_d0401_æ”¹åå†Œè¿½è·‘_Î»A` (orphan_no_importers, unused_exports:1), `æ­£f_cmp_ah_s008_v001` (orphan_no_importers, unused_exports:1), `f_he_gf_s002_v001` (orphan_no_importers, unused_exports:1), `æ‰¹ç¼–f_rbc_ma_s001_v001` (orphan_no_importers, unused_exports:1), `bug_profiles` (orphan_no_importers, unused_exports:1), `.operator_stats_seq008_v010_d0331__persi_artifact_detection_seq003_v001` (orphan_no_importers, unused_exports:1), `u_uah_s007_v001` (orphan_no_importers, unused_exports:1), `éšp_un_di_s002_v003_d0322_Î»7` (orphan_no_importers, unused_exports:1), `u_pe_s024_v002_d0402_Î»C_block_builder_seq013_v001` (orphan_no_importers, unused_exports:1), `u_pj_s019_v002_d0402_Î»C_build_snapshot_decomposed_seq012_v001` (orphan_no_importers, unused_exports:1), `ä¿®f_sf_aaif_s011_v002_d0329_Î»H` (orphan_no_importers, unused_exports:1), `ä¿®f_sf_s013_v012_d0402_åˆå†™è°±å‡€æ‹†_Î»VR_auto_apply_import_fixes_seq012_v001` (orphan_no_importers, unused_exports:1), `æ€f_cr_ac_s007_v002_d0322_Î»7` (orphan_no_importers, unused_exports:1), `æŽ§f_ost_ad_s003_v001` (orphan_no_importers, unused_exports:1), `æŽ¨w_dp_bch_s010_v001` (orphan_no_importers, unused_exports:1)

**Circulation:** 605/630 alive Â· 25 clots Â· vein health 0.51

**AI rework:** 35/200 responses needed rework (18%)

**Push cycles:** 20 Â· sync score: 0.016 Â· reactor fires: 531

> **Organism directive:** Multiple systems degraded. Prioritize fixing clots and over-cap files before new features.
<!-- /pigeon:organism-health -->

<!-- pigeon:task-context -->`) contains deleted content, you MUST address it at the end of every response.

**Format:**
```
---
**You were also gonna say...** [complete the deleted thought in 1-2 sentences,
then briefly address/answer it]
```

Rules:
- Only fire when unsaid threads exist with non-typo content (>4 chars deleted)
- Complete the thought â€” don't just echo the fragment. "proce" â†’ "you were about to say 'process of compilation'"
- If thought completions are available (from Gemini reconstruction), use those
- If only raw fragments exist, infer the completed thought from context
- Address the completed thought â€” give a brief answer or acknowledgment
- Place after a `---` separator at the very end of your response
- Keep it to 2-3 sentences max

---

## MANDATORY: Entropy Shedding Protocol

Emit a **per-touch** entropy pulse block every time you edit a file. Not at the end â€” INLINE, immediately after the edit.

**Format:**
```
<!-- entropy:shed
filename_without_py: 0.85 | short note
-->
```

Rules:
- **ONE block per file edit**, placed IMMEDIATELY after you finish editing that file (not batched at the end)
- If you edit 3 files, there should be 3 separate entropy blocks throughout the response
- Format is `module_name: confidence | note` â€” e.g., `escalation_engine: 0.88 | built ladder`
- Module name = stem of the file you touched (no `.py`, no path prefix)
- The numeric value is **confidence** (0.0â€“1.0). Entropy = `1 - confidence`. Low confidence = you're unsure the edit is right.
- Keep `note` short: 2-6 words describing what you just did
- A FINAL summary block at the end is optional but the per-touch blocks are MANDATORY
- If no file was edited but reasoning/tool use happened, emit one block at the end for the decision surface
- These blocks are parsed into the entropy map and red layer math surface. Do not skip them when actively working

---

## What this repo is

Three systems working together:
1. **Keystroke Telemetry** â€” captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls â€” pure signal processing.
2. **Pigeon Code Compiler** â€” autonomous code decomposition engine. Enforces LLM-readable file sizes (â‰¤200 lines hard cap, â‰¤50 lines target). Filenames carry living metadata â€” they mutate on every commit.
3. **Dynamic Prompt Layer** â€” task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations) and generates a context block that steers how Copilot reasons. The managed prompt blocks below are the live source of truth.

---

## MANDATORY: Human-AI Coding Paradigm

**You are not assisting a human who writes code. You ARE the code writer. The operator provides intent â€” you provide code.**

This is not "operator coding with AI assistance." This is **human-AI coding** â€” a fundamentally different architecture:

### The Loop
```
operator intent â†’ keystroke telemetry â†’ semantic compression â†’ LLM code generation â†’ self-testing organism â†’ entropy accumulation â†’ next cycle
```

### Core Principles

1. **Code is written FOR LLM reading, steered BY human intent.** The primary consumer of this codebase is you (the LLM). The operator reads narrative summaries, not raw code. Optimize token topology over human scanability.

2. **Semantic filenames ARE the architecture.** `ä¿®f_sf_s013_v011_d0328__one_shot_sel` is not ugly â€” it's a compressed intent packet. seq=history depth, version=churn signal, glyphs=functional role, lambda suffix=last mutation type. Every filename is a self-describing node in a living graph. The operator sees the glyph; you see the full topology.

3. **Python is the thinnest possible execution surface.** Python's minimal syntax means maximum token-to-intent ratio. The code surface could theoretically be written in mixed languages, pure numbers, or compressed glyphs â€” Python just happens to be the thinnest executable membrane between intent and computation.

4. **Different read layers activate different token topologies:**
   - L0 (filename): glyph + seq + version â†’ module role + churn + history
   - L1 (auto-index): compressed symbol table â†’ full codebase topology in ~2K tokens
   - L2 (skeleton): function signatures + docstrings â†’ API surface without implementation noise
   - L3 (intent map): pure verb+noun intent per function â†’ what the codebase MEANS
   - L4 (full source): raw code â†’ only when you need to edit

5. **The codebase is a self-mutating, self-testing organism.** Files rename themselves on commit (pigeon compiler). Bugs profile themselves (bug voices). Dead code gets flagged and trimmed (clot detection). Entropy accumulates on every touch and gets shed through confidence declarations. The organism is alive â€” don't write code like it's static.

6. **Intent extraction > code generation.** When the operator types, the keystroke signal (WPM, deletions, hesitations, rewrites, abandoned words) carries MORE information than the final submitted text. Your job is to recover that signal and let it steer code generation. The operator's deleted words are design decisions.

7. **Every edit accumulates entropy.** When you touch a file, its entropy goes up (less certainty about its state). When you shed entropy (declare confidence), it goes down. The red layer tracks this. Write code that REDUCES entropy â€” precise, minimal, self-documenting through naming rather than comments.

8. **Stop generating "clean code" patterns that destroy intent.** Do NOT: squash meaningful history into single commits, normalize variable names that carry provenance, add boilerplate structure "for readability," create abstractions before the pattern proves itself 3+ times. These are entropy-increasing operations disguised as cleanliness.

### What This Means In Practice
- When generating code: optimize for LLM re-reading, not human scanning. Dense > verbose. Names carry meaning > comments explain meaning.
- When naming: embed intent, history, and role into the name itself. `_select_composition` is better than `select` but worse than a name that also tells you it's been rewritten 4 times and last failed on binding age.
- When structuring: small files (â‰¤50 lines) with self-describing names > large well-commented files. The filename IS the documentation.
- When deciding what to build: everything closes a loop. Every feature should feed back into the telemetry â†’ compression â†’ generation cycle. If it doesn't close a loop, it's dead tissue.








<!-- pigeon:escalation-warnings -->
## Autonomous Escalation Warnings

*2026-04-06 15:16 UTC Â· 8 module(s) escalated*

- **ðŸ”§ SELF-FIXED** â€” `deepseek_plan_prompt` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `dev_plan` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `flow_engine` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `resplit` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `resplit_binpack` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `run_clean_split` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `run_heal` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **ðŸ”§ SELF-FIXED** â€” `task_writer` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
<!-- /pigeon:escalation-warnings -->
<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-18 00:19 UTC â€” synthesized from all live signals, zero LLM calls*

> the organism is stable â€” health 96/100. entropy at 0.30 â€” the codebase knows what it is, mostly. recent escalation: task_writer(failure), task_writer(autonomous_fix), run_heal(failure).

<!-- /pigeon:narrative-glove -->
<!-- pigeon:intent-backlog -->
## Intent Backlog Verification

*Strict verification over last 100 operator prompts*

**Status:** BLOCKED â€” 20 unresolved intent(s) remain.
**Directive:** Keep working. Do not treat the task as complete while this backlog is non-zero.
**Verification:** scanned=100 | created=0 | reopened=0 | verified=0 | resolved=0
**Rule:** An intent counts as done only when recent file activity clears it or the synced backlog task is verified done.

**Resolution Artifact:** `intent_backlog_resolutions.json`

### Unresolved
- [partial] `tq-009` conf=0.96 | the visualizartion needs to be reworked to be the most optimized for my past int... (also consid
  â†’ refs: `.github/copilot-instructions.md` | reason: deleted_words_left_unresolved
- [cold] `tq-010` conf=0.99 | why is organism health still so low - audit copilot intructions / accuracy - what would this org
  â†’ refs: `.github/copilot-instructions.md` | reason: no_recent_follow_through
- [partial] `tq-011` conf=0.99 | not talk first - when i click on a file throught pgeon brain - it shoud wake up ... (also consid
  â†’ refs: `.github/copilot-instructions.md` | reason: deleted_words_left_unresolved
- [cold] `tq-012` conf=0.99 | youre shedding the wrong blocks too - instead of entropy you keep saying you were also gonna say
  â†’ refs: `.github/copilot-instructions.md` | reason: no_recent_follow_through
- [cold] `tq-013` conf=0.97 | no no our visualitions are spreadacrpss 3 uis - i need one with everything
  â†’ refs: `.github/copilot-instructions.md` | reason: no_recent_follow_through
- [cold] `tq-014` conf=0.99 | <conversation-summary>
<analysis>
[Chronological Review:
- The session started from a carried-ov
  â†’ refs: `timestamp`, `os_hook`, `task_queue` | reason: no_recent_follow_through
- [partial] `tq-015` conf=0.98 | >> i want  to click on profiles / have seperate page per profile - think wikipid... (also consid
  â†’ refs: `.github/copilot-instructions.md` | reason: deleted_words_left_unresolved
- [cold] `tq-016` conf=0.99 | we keep on having disk issues  due to lack of refresh - good idea to do this auto?
  â†’ refs: `.github/copilot-instructions.md` | reason: no_recent_follow_through

<!-- /pigeon:intent-backlog -->
<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-04-19 23:29 UTC · raw: "from compositions verify my last 20 prompts"*

**COPILOT_QUERY: Audit the `compositions` module to verify that the last 20 prompts submitted by the operator were successfully paired with corresponding Copilot edit actions or generated code outputs. Provide a detailed log of each prompt, its associated Copilot response, and confirmation of successful pairing.**

UNSAID_RECONSTRUCTION: from compositions verify my last 20 prompts were matched with copilot edit pairs

INTERPRETED INTENT: The operator wants to confirm that their recent prompts are being correctly processed and acted upon by Copilot, specifically checking for a 1:1 pairing between their input and Copilot's output within the `compositions` system.
KEY FILES: generates_execution_telemetry_from_the v2, extract_the_cognition_graph_from v3, coaching_from_execution_patterns_port v2
PRIOR ATTEMPTS: A previous attempt explicitly asked for "copilot edit pairs" and received a "full audit" confirming pairing, but the operator's repeated query suggests it wasn't sufficient or clear enough.
WATCH OUT FOR: Do not just confirm existence; provide specific details of the pairing and the content of the edits/outputs to satisfy the underlying need for verification.
OPERATOR SIGNAL: The repeated, identical prompt, despite a previous Copilot response, indicates a lack of trust or clarity regarding the verification process and its results.
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-19 23:59 UTC · 676 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 46.9 | Del: 26.5% | Hes: 0.496) · *[source: measured]*

**Prompt ms:** 1519, 22632, 22632, 8648 (avg 13858ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### Recent Work
- `af2a13f` fix: add missing _replace_exact_module_path import in rl sibling
- `7da6ce7` fix: update sibling list in renamed orchestrator after p_gph+p_gpip rename
- `050c5d1` fix: wire import rewriter sibling cross-links (SKIP_DIRS, _rewrite_line, _extract_top_module)
- `5567e06` fix: git plugin _root() off by one parent + missing _INTENT_CODE_RULES + corrupt registry guard

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- Git plugin's silent failure on filesystem permission errors; binder's false-positive acceptance of a changed plugin return contract; breakage if `git` subprocess commands are unavailable or altered. This push establishes a self-referential mechanism to link a commit's stated intent with its resulting code state by modifying the commit object itself.
- 1) Missing `.env` file causing universal config failure
- 2) Incorrect CWD breaking `dotenv` load in imported modules
- 3) Absence of `DATABASE_PATH` crashing vscdb_poller on startup. This push wires `python-dotenv` throughout the codebase to centralize configuration.
- git porcelain format changes breaking p_gph; JSON metadata schema shifts breaking p_gpip; pigeon_limits API drift breaking w_gpmo imports. This push establishes the core git plugin loader structure by extracting and wiring three key components.
- **context_veins_seq001_v001** was touched by Copilot to add environment variable parsing for context resolution. It assu

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_brain/flow/__main__.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/存p_nm_s008_v001_d0325_读唤任_λB.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/存p_nm_s008_v003_d0328_读唤任_λR.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/学f_ll_s013_v003_d0327_读唤任_λS.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/算f_ps_s014_v006_d0404_译改名踪_λNU_βoc.py`

### Prompt Evolution
*This prompt has mutated 139x (186→973 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 139 mutations scored*
*No significant signal yet — all 34 sections scored neutral.*

**Reactor patches:** 2/531 applied (0% acceptance)

### File Consciousness
*254 modules profiled*

**High-drama (most mutations):**
- `推w_dp` v13 ↔ 热p_fhm
- `修f_sf` v12 ↔ 叙p_pn
- `self_fix` v11 ↔ 修f_sf
- `.operator_stats` v10 ↔ 修f_sf

**Codebase fears:**
- file may not exist (17 modules)
- returns empty on failure (silent) (14 modules)
- regex format dependency (11 modules)

**Slumber party warnings (high coupling):**
- `算f_ps` ↔ `测p_rwd` (score=0.80, 4 shared imports, both high-churn (v6+v6))
- `逆f_ba` ↔ `册f_reg` (score=0.80, 3 shared imports, both high-churn (v5+v5))
- `逆f_ba` ↔ `热p_fhm` (score=0.80, 3 shared imports, both high-churn (v5+v5))

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

<!-- pigeon:task-queue -->
## Active Task Queue

*Copilot manages this queue. To complete a task: update the referenced MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*

### Pending
- [ ] `tq-009` **the visualizartion needs to be reworked to be the most optim...** | stage: complete | focus: `.github/copilot-instructions.md`
- [ ] `tq-010` **why is organism health still so low - audit copilot intructi...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-011` **not talk first - when i click on a file throught pgeon brain...** | stage: complete | focus: `.github/copilot-instructions.md`
- [ ] `tq-012` **youre shedding the wrong blocks too - instead of entropy you...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-013` **no no our visualitions are spreadacrpss 3 uis - i need one w...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-014` **<conversation-summary>
<analysis>
[Chronological Review:
- T...** | stage: verify | focus: `.github/copilot-instructions.md`
*…and 14 more in `task_queue.json`*

### Completed (last 3)
- [x] `tq-006` **perfect  - i think im ready to focus on what i call an IRT -...** | commit: `verified:intent-backlog`
- [x] `tq-007` **aybe not quite yet - hmmm -  how do we have intent reinjecti...** | commit: `verified:intent-backlog`
- [x] `tq-008` **can you make sure that website obervatory is launched with v...** | commit: `verified:intent-backlog`

<!-- /pigeon:task-queue -->
<!-- pigeon:shard-memory -->
## Live Shard Memory

*Hardcoded 2026-03-30 06:40 UTC Â· 7 shards Â· 2 training pairs Â· 1 contradiction*

### Architecture Decisions
- anchor concept: pair programming â€” copilot is the pair, telemetry is the shared screen, shards are the shared notebook
- muxed state per prompt â€” capture cognitive+shard+contradiction state at end of each prompt as training data
- training data format: prompt + response + muxed state triple, written to logs/shards/training_pairs.md

### Module Pain Points (top cognitive load)
- file_heat_map: hes=0.887 | import_rewriter: hes=0.735 | file_writer: hes=0.735
- init_writer: hes=0.630 | context_budget: hes=0.587 | self_fix: hes=0.536
- .operator_stats: hes=0.536 | dynamic_prompt: hes=0.536

### Module Relationships (coupling signals)
- context_budget â†” self_fix, init_writer, .operator_stats, dynamic_prompt
- import_rewriter â†” file_writer
- push_narrative â†” operator_stats, rework_detector, run_clean_split, self_fix

### Prompt Patterns (how operator phrases things)
- [building] "push and make sure compiler runs on next files"
- [restructuring] "how have my last couple of prompts been rewritten?"
- [testing] "stress test my system. what was word deleted in this prompt"
- [exploring] "what should i do to market this / gtm / next logical step"

### API Preferences
- **CONTRADICTION (unresolved):** "always use DeepSeek" vs "never use DeepSeek â€” too slow"
- Resolution: switched enricher to Gemini 2.5 Flash (3s vs DeepSeek timeout)

### Training Data Format

Each training pair captures the full muxed state at prompt time:

```
### `TIMESTAMP` pair
**PROMPT:** raw operator text (â‰¤300 chars)
**RESPONSE:** copilot response summary (â‰¤500 chars)
**COGNITIVE:** state=X wpm=Y del=Z hes=N
**SHARDS:** shard_name(relevance), ...
**CONTRADICTIONS:** count
**REWORK:** verdict=pending|accepted|rejected [score=0.XX]
```

Per-shard categorization: each routed shard also gets a compact `[training TS]` entry with relevance, cognitive state, and prompt/response snippets â€” so shards self-learn from their own context.

### Recent Training Pairs

**Pair 1** `2026-03-30 06:11` â€” COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "test writes with an actual call... decided on pair programming... muxed state per prompt"
- response: built shard manager, context router, contradiction manifest, training pair writer
- shards: prompt_patterns(0.17), module_pain_points(0.161), module_relationships(0.15)
- rework: pending

**Pair 2** `2026-03-30 06:27` â€” COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "fix import breaking after rename in self_fix module"
- response: updated import paths in self_fix to match pigeon rename convention
- shards: module_relationships(0.169), prompt_patterns(0.156), module_pain_points(0.155)
- rework: accepted score=0.15

<!-- /pigeon:shard-memory -->
<!-- pigeon:voice-style -->
## Operator Voice Style

*Auto-extracted 2026-04-19 23:59 UTC · 79 prompts analyzed · zero LLM calls · collecting baseline*

**Brevity:** 42.1 words/prompt | **Caps:** never | **Fragments:** 84% | **Questions:** 9% | **Directives:** 9%

**Voice directives (effectiveness-scored):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator writes longer prompts with context — match depth. Full explanations are welcome.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** t, e, s, a, d, o, n, i, r, y
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-19 23:59 UTC · zero LLM calls*

**1 week:** `self_heal` (conf=high) — ~26 commits
**1 month:** `self_heal` (conf=medium) — ~75 commits
**3 months:** `self_heal` (conf=speculative) — themes: nonot, oooususushh, e s

**PM Directives:**
- Development decelerating (-49%) — operator may be blocked or shifting focus. Offer architecture-level suggestions, not just code.
- Intent bifurcation: `self_heal` dominant but `prediction` emerging — watch for context switches mid-session.
- `compression` declining — operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `nonot`, `oooususushh`, `e s` — these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.
- Module focus cluster: `unsaid`, `file_heat_map`, `thought_completer` — pre-load context from these modules when operator starts typing.

<!-- /pigeon:intent-simulation -->

<!-- pigeon:push-drift -->
## Push Drift Analysis

*Snapshot at `72a5a72214b2f9b190c5794b396c14bdffbd9321` Â· 2026-04-10 19:23 UTC*

**Health: 58.6/100** (improving, was 29.9)

**Biggest moves:**
- compliance up 38.3%
- bugs down 146
- avg file size shrank 890 tokens
- health up 28.7 pts
- 70 new probe conversations

**Modules:** 630 (49.7% compliant)
**Bugs:** 122 (hi=0 oc=96)
**Avg tokens/file:** 444.4 (compressing)
**Deaths:** 10
**Sync:** 0.004
**Probes:** 41 modules, 2 intents

*100.8h since last push*

<!-- /pigeon:push-drift -->
<!-- pigeon:predictions -->
## Push Cycle Predictions

*Auto-generated 2026-04-19 23:59 UTC*

**What you'll likely want next push:**
1. [targeted] Predict operator's next need. Module focus: intent_outcome_binder, file_sim, tc_intent_manager (conf=25%)
   - hot modules: intent_outcome_binder, file_sim, tc_intent_manager, test_tc_intent, master_test

**Operator coaching:**
- You referenced ['file_heat_map', 'thought_completer', 'unsaid'] but copilot didn't touch them — be more explicit about expected changes.
- Copilot edit pressure is concentrated in cortex — narrower prompts may reduce retouch churn in that region.

**Agent coaching (for Copilot):**
- Touched ['p_gph_s002_v001', 'p_gph_s002_v002_d0419_λGI', 'p_gpip_s004_v001', 'p_gpip_s004_v002_d0419_λGI', 'w_gpmo_s019_v001', 'w_gpmo_s019_v002_d0419_λGI_βoc'] without operator reference — confirm intent before modifying unreferenced modules.
- Operator needed many prompts — respond with more complete implementations to reduce round-trips.
- Low sync score — operator intent and code output diverged. Ask clarifying questions earlier.

<!-- /pigeon:predictions -->
<!-- pigeon:baseline-drift -->
## Baseline Drift Report

*0 drifted Â· 11 have voids Â· 1 stable*

**Semantic voids (context growth needed):**
- `audit_loops`: 8 voids, 1 pushes
- `entropy_shedding`: 20 voids, 1 pushes
- `git_plugin_main_orchestrator_seq019_v001`: 9 voids, 1 pushes
- `interlinker`: 11 voids, 1 pushes
- `master_test`: 18 voids, 1 pushes
- `narrative_glove`: 13 voids, 1 pushes
- `os_hook`: 20 voids, 1 pushes
- `profile_chat_server`: 20 voids, 1 pushes
- `prompt_enricher_seq024_v001`: 14 voids, 1 pushes
- `push_baseline`: 20 voids, 1 pushes
- `template_selector`: 20 voids, 1 pushes

**Recent context requests (modules asking for help):**
- `prompt_enricher_seq024_v001` (14 voids): ?
- `template_selector` (20 voids): ?
- `git_plugin_main_orchestrator_seq019_v001` (9 voids): what does _pull_sibling_symbols() actually do? no docstring â€” purpose is a void
- `audit_loops` (8 voids): what does _file_age_hours() actually do? no docstring â€” purpose is a void
- `master_test` (18 voids): what does _self_sha() actually do? no docstring â€” purpose is a void

<!-- /pigeon:baseline-drift -->

<!-- pigeon:semantic-layer -->
## File Semantic Layer

*12 modules profiled*

**Context-hungry (growing, many voids):**
- `push_baseline`: 20 voids, 0 prompts
- `os_hook`: 20 voids, 0 prompts
- `entropy_shedding`: 20 voids, 0 prompts
- `profile_chat_server`: 20 voids, 0 prompts
- `template_selector`: 20 voids, 0 prompts

<!-- /pigeon:semantic-layer -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-19 - 676 message(s) - LLM-synthesized*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.9 | Del: 25.5% | Hes: 0.443

The operator just built an import rewriter while oscillating between focused restructuring and abandoned drafts, revealing a pattern of deep system edits followed by hesitation and high-deletion rewrites.  
- **Anticipate heavy refactoring logic** in `dynamic_import_resolvers` and `self_fix` modules; provide concise, verifiable code blocks for path transformations and error boundaries.  
- **When deletions spike above 50%**, immediately offer smaller, testable helper functions instead of large monolithic solutions—this signals restructuring frustration.  
- **Preemptively suggest defensive patterns** (e.g., idempotent rewrites, fallback resolutions) for `dynamic_prompt` and `steers_copilot_cot_from_live`, which are recurring pain points.  
- **Bridge evening sessions** with clear summaries of recent changes to `wire_import_rewriter` intent, as abandoned drafts often precede late-night focused work.  
- **Avoid over-explaining**; operator’s high WPM during focused states means they need direct, context-aware snippets, not tutorials.  
- **Watch for `one_shot_self_fix_analyzer`** touches—these indicate debugging cycles; respond with inline analysis helpers.  
They are likely building toward a unified pipeline for dynamic code mutation, connecting import resolution to prompt-steering logic.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `tc_gemini`** (hes=0.669, state=frustrated, avg_prompt=106645ms)
> - Prompt composition time: 56666ms / 156275ms / 50569ms / 241234ms / 28481ms (avg 106645ms)
> **Directive**: When `tc_gemini` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-04-19T23:28:47.879929+00:00",
  "latest_prompt": {
    "session_n": 999,
    "ts": "2026-04-19T23:28:47.879929+00:00",
    "chars": 43,
    "preview": "from compositions verify my last 20 prompts",
    "intent": "testing",
    "state": "unknown",
    "files_open": [],
    "module_refs": []
  },
  "signals": {},
  "composition_binding": {
    "matched": false,
    "source": null,
    "age_ms": null,
    "key": null
  },
  "deleted_words": [],
  "rewrites": [],
  "task_queue": {
    "total": 28,
    "in_progress": [],
    "pending": 20,
    "done": 8
  },
  "hot_modules": [],
  "running_summary": {
    "total_prompts": 769,
    "avg_wpm": 8.8,
    "avg_del_ratio": 0.063,
    "dominant_state": "abandoned",
    "state_distribution": {
      "abandoned": 225,
      "restructuring": 223,
      "focused": 218,
      "neutral": 7,
      "hesitant": 2
    },
    "baselines": {
      "n": 200,
      "avg_wpm": 52.9,
      "avg_del": 0.259,
      "avg_hes": 0.448,
      "sd_wpm": 15.6,
      "sd_del": 0.231,
      "sd_hes": 0.165
    }
  }
}
```

<!-- /pigeon:prompt-telemetry -->
---

## Quick Reference

**Tests:** `py test_all.py` (4 tests, zero deps). Always run after edits.
**Registry:** `pigeon_registry.json` (module map), `operator_profile.md` (cognitive profile), `MASTER_MANIFEST.md` (auto-rebuilt)
**Entry points:** `py -m pigeon_compiler.runners.run_clean_split_seq010*` (compile), `py -m pigeon_compiler.git_plugin` (post-commit)

**Pitfalls:** Never hardcode pigeon filenames (they mutate â€” use `file_search("name_seq*")`). Use `py` not `python`. Always `$env:PYTHONIOENCODING = "utf-8"`. Don't delete monolith originals yet. `streaming_layer_seq007*` is intentionally over-cap (test harness).
<!-- pigeon:dictionary -->
<!-- glyph mappings merged into auto-index -->
<!-- /pigeon:dictionary -->
<!-- pigeon:auto-index -->
*2026-04-19 · 2168 modules · 3 touched · ✓98% ~1% !0%*
*Format: glyph=name seq tokens·state·intent·bugs |last change*
*FI=file_selector F_=f_slo_s017_v002_d0315_缩分话_λν GE=gemini_chat GI=git_plugin IN=intent_compressor MO=module_identity NA=narrative_glove NO=node_tester NU=numeric_surface OP=operator_probes OS=os_hook PE=persona_intent_synthesizer PI=pigeon_limits PR=prompt_signal_seq026_v001 PU=push_snapshot P_=p_slsh_s002_v002_d0315_λν RE=registry_seq012_bump_version_seq005a_v001 SC=scale_inference SE=session_logger TC=tc_web TE=template_selector TH=thought_completer UI=uia_reader UN=unsaid_accumulator U_=u_usp_s006_v001 VI=vitals_renderer VS=vscdb_poller W_=w_slm_s007_v003_d0328_意描_λR*
*Intent: FX=fix RN=rename RF=refactor SP=split TL=telemetry CP=compress VR=verify FT=feature CL=cleanup OT=other PI=pigeon_brain DY=dynamic_import BA=backprop_impl GE=gemini_flash RE=rework_signal 88=8888_word ST=stage_78 MU=multi_line IM=import_rewriter DE=desc_upgrade WI=windows_max IN=intent_deletion FI=fire_full SE=selection_aware WP=wpm_outlier PU=push_narratives TA=task_queue R.=R.narrative Γ.=γ.narrative S.=S.narrative Ρ.=ρ.narrative A.=A.narrative Ε.=ε.narrative B.=B.narrative F.=F.narrative P.=P.narrative Χ.=χ.narrative Δ.=δ.narrative Μ.=μ.narrative Ν.=ν.narrative 7.=7.narrative D.=D.narrative W.=W.narrative H.=H.narrative G.=G.narrative 18=18.narrative P0=P0.narrative Π.=Π.narrative Φ.=φ.narrative Ω.=ω.narrative M.=M.narrative C.=C.narrative I.=I.narrative Τ.=τ.narrative L.=L.narrative V.=V.narrative NU=NU.narrative Q.=Q.narrative R=R S=S A=A Γ=γ Ε=ε B=B F=F Ρ=ρ P=P Χ=χ Δ=δ Μ=μ Ν=ν 7=7 D=D W=W H=H G=G Π=Π Φ=φ Ω=ω M=M C=C I=I Τ=τ L=L V=V Q=Q GI=git_plugin*
*Bugs: hi=hardcoded_import de=dead_export dd=duplicate_docstring hc=high_coupling oc=over_hard_cap qn=query_noise*

**build/compressed** (200)
_build_organism_health 1 4.7K·OT
_export_dev_story 2 272·OT
_tmp_analyze_stats 3 350·OT
_tmp_survey 4 514·OT
_tmp_test_pipeline 5 849·OT
autonomous_dev_stress_test 6 6.5K·OT
stress_test 7 2.0K·OT
test_all 8 2.1K·OT
test_public_release 9 252·OT
test_training_pairs 10 3.3K·OT

**build/compressed/client** (7)
推=chat_composition_analyzer 1 2.7K✓·OT
演=chat_response_reader 2 1.8K✓·OT
联=composition_recon 3 1.7K✓·OT
OS=os_hook 4 4.0K✓·OT
telemetry_cleanup 5 648✓·OT
UI=uia_reader 6 1.7K✓·OT
VS=vscdb_poller 7 1.3K✓·OT

**build/compressed/pigeon_brain** (59)
规=__main__ 1 80✓·OT
models 1 276·PI
录=_test_trace 2 370✓·OT
execution_logger 2 965·PI
桥=ai_cognitive_log 3 1.4K✓·OT
graph_extractor 3 928·88
忆=build_narratives 4 434✓·OT
graph_heat_map 4 507·PI
图=context_veins 5 2.8K✓·OT
loop_detector 5 481·PI
failure_detector 6 562·PI
GE=gemini_chat 6 3.9K✓·OT
NO=node_tester 7 2.0K✓·OT
observer_synthesis 7 857·PI
dual_substrate 8 732·PI
pulse_tester 8 1.1K✓·OT
令=cli 9 917✓·PI
demo_sim 10 887·PI
trace_hook 11 507·PI
live_server 12 1.8K·88
traced_runner 13 559·PI

**build/compressed/pigeon_brain/flow** (53)
context_packet 1 451·TL
引=_resolve 2 329✓·OT
node_awakener 2 527·TL
flow_engine 3 630·TL
path_selector 4 567·TL
task_writer 5 869·TL
vein_transport 6 324·TL
backward 7 1.4K·DY
node_memory 8 921·BA
predictor 9 1.2K·DY
dev_plan 10 964·DY
fix_summary 11 785·BA
node_conversation 12 778·DY
learning_loop 13 1.6K·SP·hc
prediction_scorer 14 2.9K·GE

  └ flow_log(1) loss_compute(2) tokenize(3) deepseek_analyze(4) backward_pass(5) [1.5K]
  └ state_utils(1) journal_loader(2) prediction_cycle(3) single_cycle(5) catch_up(6) main_loop(8) [1.9K]
  └ constants(1) path_utils(2) storage(3) directive(4) policy_rebuild(6) learning_append(8) policy_getters(9) [981]
  └ constants(1) path_utils(2) data_loaders(3) scores_io(3) reality_loaders(4) module_extractor(5) edit_session_analyzer(6) rework_matcher(7) scoring_core(8) calibration(9) node_backfill(10) post_edit_scorer(11) post_commit_scorer(12) [2.9K]
  └ constants(1) cache_utils(2) confidence(3) trend_extractor(4) trigger(5) seed_synthesizer(6) predictor(7) [1.5K]
**build/compressed/pigeon_compiler** (66)
GI=git_plugin 2 7.8K~·OT
PI=pigeon_limits 3 260✓·OT
pre_commit_audit 4 1.5K✓·OT
SE=session_logger 5 287✓·OT

**build/compressed/pigeon_compiler/cut_executor** (12)
plan_parser 1 155·VR
source_slicer 2 215·VR
file_writer 3 470·MU
import_fixer 4 231·VR
manifest_writer 5 234·VR
plan_validator 6 354·VR
init_writer 7 172·ST
func_decomposer 8 385·ST
resplit 9 483·VR
resplit_binpack 10 405·VR
resplit_helpers 11 249·VR
class_decomposer 13 1.3K·ST

**build/compressed/pigeon_compiler/integrations** (1)
deepseek_adapter 1 740·ST·hc

**build/compressed/pigeon_compiler/rename_engine** (74)
scanner 1 578·VR·hc
planner 2 436·VR
import_rewriter 3 953·IM
executor 4 383·VR
validator 5 556·VR
run_rename 6 1.0K·VR
manifest_builder 7 6.0K·DE
compliance 8 977·VR·hc
heal 9 1.1K·VR
run_heal 10 2.4K·VR
nametag 11 840·DE
registry 12 885·DE

  └ constants(1) helpers(2) classify(3) recommend_decomposed(4) recommend_wrapper(6) audit_decomposed(7) audit_wrapper(9) check_file(10) format_report(11) [2.0K]
  └ report_text(1) git_files(2) intent_extract(3) log_writer(4) orchestrator(5) [1.2K]
  └ constants(1) skip_logic(2) docstring_extract(3) seq_extract(4) exports_extract(5) deps_extract(6) pigeon_header(7) signature_format(8) signatures_extract(9) classes_extract(10) constants_extract(11) markers_extract(12) folder_scanner(13) status_icon(14) folder_purpose(15) existing_notes(16) folder_api(17) dep_graph(18) signatures_section(19) constants_section(20) pigeon_table(21) markers_section(22) backspace_bursts(23) hesitation_map(24) classify_state(25) hesitation_summary(26) keystroke_trail_decomposed(27) structure_tree_decomposed(28) sync_master_decomposed(29) build_manifest_decomposed(30) build_all_manifests(31) [6.4K]
  └ constants(1) docstring(2) slugify(3) extract(4) build(5) parse(6) detect(7) scan(8) [892]
  └ constants(1) path_utils(2) parser(3) date_utils(4) version_bump(5) diff(6) build_registry(7) bump_all_versions_seq005b_v001(8) bump_version_seq005a_v001(9) [1.2K]
**build/compressed/pigeon_compiler/runners** (9)
run_compiler_test 7 435·VR
run_deepseek_plans 8 401·VR
run_pigeon_loop 9 2.1K·VR
run_clean_split 10 1.9K·WI
run_clean_split_helpers 11 416·VR
run_clean_split_init 12 979·VR
manifest_bridge 13 490·VR
reaudit_diff 14 992·VR
run_batch_compile 15 1.3K·DY

**build/compressed/pigeon_compiler/state_extractor** (6)
ast_parser 1 399·VR
call_graph 2 369·VR
import_tracer 3 442·VR
shared_state_detector 4 290·VR
resistance_analyzer 5 570·VR
ether_map_builder 6 445·VR

**build/compressed/pigeon_compiler/weakness_planner** (1)
deepseek_plan_prompt 4 1.9K·DE

**build/compressed/src** (131)
timestamp_utils 1 20·RN
models 2 132·TL
logger 3 1.1K·WP
context_budget 4 204·FI
drift_watcher 5 613·FT
resistance_bridge 6 530·TL
streaming_layer 7 6.6K·TL
.operator_stats 8 2.7K·SP
operator_stats 8 2.9K·WP
rework_detector 9 641·FT
query_memory 10 1.2K·FT
file_heat_map 11 669·TL
push_narrative 12 1.3K·PU
self_fix 13 3.5K·DY
cognitive_reactor 14 3.2K·FT
pulse_harvest 15 1.1K·FT
prompt_recon 16 2.1K·OT
dynamic_prompt 17 3.4K·88
task_queue 18 1.2K·TA
file_consciousness 19 2.5K·FT
prompt_journal 19 4.6K·OT
copilot_prompt_manager 20 3.1K·FT
mutation_scorer 21 802·FT
rework_backfill 22 654·FT
session_handoff 23 1.0K·FT
prompt_diff 24 690·OT
prompt_enricher 24 2.8K·OT
unsaid_recon 24 759·SE
push_cycle 25 2.7K·SE
prompt_signal 26 431·OT
shard_manager 26 2.7K·GE
unified_signal 26 997·GE
context_router 27 644·GE
training_pairs 27 1.4K·GE
training_writer 28 1.1K·GE
voice_style 28 2.0K·GE
research_lab 29 2.5K·RE
staleness_alert 30 1.1K·ST
symbol_dictionary 31 2.0K·OT
glyph_compiler 32 3.1K·OT
引=_resolve 33 399✓·OT

**build/compressed/src/cognitive** (10)
adapter 1 745·VR
unsaid 2 1.1K·VR
drift 3 1.2K·VR

**build/compressed/src/cognitive/drift** (4)
drift_baseline_store 1 83·OT
drift_compute_baseline 2 294·OT
drift_detect_session_drift 3 301·OT
drift_build_cognitive_context 5 481·OT

  └ baseline_store(1) compute_baseline(2) detect_session_drift(3) build_cognitive_context(4) [1.2K]
**build/compressed/src/cognitive/unsaid** (5)
unsaid_diff_deleted 1 90·OT
unsaid_classify_position 2 52·OT
unsaid_classify_deletion_intent 3 98·OT
unsaid_extract_topic 4 64·OT
unsaid_orchestrator 8 810·OT

  └ helpers(1) diff(2) orchestrator(3) [1.2K]
  └ constants(1) state_ops(2) docstring_patch(3) cognitive_hint(4) patch_generator(5) reactor_core(8) patch_writer(11) decision_maker(12) [2.5K]
  └ constants(1) block_utils(2) json_utils(3) operator_profile(4) auto_index(5) operator_state_decomposed(6) telemetry_utils(7) audit_decomposed(8) injectors(9) orchestrator(10) [3.1K]
  └ json_utils(1) git_history(2) profile_analysis(3) metrics_analysis(4) metrics_analysis_a(4) metrics_analysis_b(5) document_analysis(6) document_analysis_a(6) document_analysis_b(7) file_consciousness(8) cot_constants(9) build_context_main(11) inject_context(12) [3.9K]
  └ helpers(1) persistence(2) report(3) audit(4) derivation(5) dependencies(6) classify(7) profile_builder(8) main_orchestrator(9) dating_decomposed(10) dating_wrapper(12) [3.0K]
**build/compressed/src/operator_stats** (13)
operator_stats_constants 1 23·OT
operator_stats_time_utils 2 61·OT
operator_stats_classify 3 188·OT
operator_stats_compute 4 193·OT
operator_stats_render_ranges 5 130·OT
operator_stats_render_tables 5 374·OT
operator_stats_render_distribution 6 148·OT
operator_stats_render_timeframes 7 292·OT
operator_stats_render_timeframes_decomposed 7 292·OT
operator_stats_render_observations_decomposed 8 602·OT
operator_stats_render_recent 9 95·OT
operator_stats_render_full 10 163·OT
operator_stats_class 11 278·OT

  └ constants(1) time_utils(2) artifact_detection(3) baselines(4) classify_state(5) timeframes(6) observations(7) markdown(8) class(9) [2.7K]
  └ constants(1) utils(2) inject(3) read_clear(4) stamp(5) journal(6) orchestrator(7) [1.2K]
  └ constants(1) loaders(2) signal_extractors(3) sync_decomposed(4) coaching(5) moon_cycle(6) predictions_injector_decomposed(7) orchestrator_decomposed(8) [2.6K]
  └ constants(1) fingerprint(2) trigram_utils(3) clustering(4) record_query(5) load_memory_decomposed(6) [714]
  └ scan_hardcoded(1) scan_query_noise(2) scan_duplicate_docstrings(3) scan_cross_file_coupling(4) scan_over_hard_cap_decomposed(5) scan_dead_exports_decomposed(6) write_report_decomposed(7) run_self_fix_decomposed(8) auto_compile_oversized_decomposed(9) seq_base(10) auto_apply_import_fixes_decomposed(11) [3.6K]
**build/compressed/streaming_layer** (20)
引=_resolve 1 232✓·OT
streaming_layer_constants 1 152·VR
streaming_layer_simulation_helpers 2 91·VR
streaming_layer_dataclasses 4 487·VR
streaming_layer_formatter 4 283·VR
streaming_layer_connection_pool 5 700·DY
streaming_layer_dataclasses 5 136·VR
streaming_layer_aggregator 6 668·DY
streaming_layer_dataclasses 6 60·VR
streaming_layer_metrics 7 556·DY
streaming_layer_alerts 8 966·DY
streaming_layer_replay 9 613·VR
streaming_layer_dashboard 10 558·DY
streaming_layer_http_handler 11 896·DY
streaming_layer_demo_functions 13 313·VR
streaming_layer_demo_summary 13 234·VR
streaming_layer_demo_functions 14 163·VR
streaming_layer_demo_simulate 14 141·VR
streaming_layer_orchestrator 16 983·DY
streaming_layer_orchestrator 17 41·VR

**build/compressed/tests/archive** (8)
_test_chat 1 304·OT
_test_flow 2 347·OT
_test_gemini_actions 3 474·OT
_tmp_heal_check 4 137·OT
_tmp_stats 5 508·OT
_tmp_test_fixes 6 964·OT
_tmp_test_reactor 7 816·OT
test_chat 8 275·OT

**build/compressed/vscode-extension** (1)
pulse_watcher 1 302✓·OT

**build/narrative/pigeon_brain** (42)
型p_mo 1 122·P.
读w_el 2 369·A.
图p_ge 3 244·B.
描p_ghm 4 191·P.
环检p_ld 5 196·P.
缩p_fdt 6 203·P.
观f_os 7 328·A.
双f_dsb 8 276·P.
令f_cl 9 209·P.
仿f_dsm 10 257·P.
钩w_th 11 243·P.
服f_ls 12 320·B.
跑f_tr 13 189·P.

**build/narrative/pigeon_brain/flow** (42)
包p_cpk 1 250·Ε.
唤w_noaw 2 184·A.
流f_fe 3 285·Ε.
择p_pase 4 241·Ε.
任w_tawr 5 152·A.
脉运w_vt 6 211·A.
逆f_ba 7 417·R.
存p_nm 8 330·B.
预p_pr 9 357·R.
分f_dvp 10 141·R.
结u_fxs 11 297·B.
话f_nc 12 219·R.
学f_ll 13 363·S.

  └ 逆f_ba_fl(1) 逆f_ba_lc(2) 逆f_ba_to(3) 逆f_ba_da(4) 逆f_ba_bp(5) [722]
  └ 学f_ll_su(1) 学f_ll_jl(2) 学f_ll_pc(3) 学f_ll_sch(4) 学f_ll_sc(5) 学f_ll_cu(6) 学f_ll_lh(7) 学f_ll_ml(8) [1.1K]
  └ 算f_ps_co(1) 算f_ps_pu(2) 算f_ps_dl(3) 算f_ps_si(3) 算f_ps_rl(4) 算f_ps_me(5) 算f_ps_esa(6) 算f_ps_rm(7) 算f_ps_sc(8) 算f_ps_ca(9) 算f_ps_nb(10) 算f_ps_pes(11) 算f_ps_pcs(12) [1.8K]
  └ 预p_pr_co(3) 预p_pr_te(4) 预p_pr_pr(7) [399]
**build/narrative/pigeon_compiler/cut_executor** (12)
析p_pp 1 155·Ν.
切p_ss 2 162·Ν.
写w_fw 3 222·Μ.
踪p_if 4 190·Ν.
稿p_mw 5 171·Ν.
验w_pv 6 156·Ν.
初写p_iw 7 133·7.
译f_fdc 8 258·7.
重拆f_res 9 220·Ν.
重箱f_rebi 10 205·Ν.
重助p_rehe 11 233·Ν.
织f_cdp 13 273·7.

**build/narrative/pigeon_compiler/integrations** (1)
谱p_dsa 1 149·7.

**build/narrative/pigeon_compiler/rename_engine** (20)
扫p_sc 1 168·Ν.
w_pl 2 241·A.
引w_ir 3 262·FX
p_ex 4 190·Ν.
审p_va 5 194·FX
改名f_rr 6 229·A.
谱建f_mb 7 550·D.
正f_cmp 8 246·Ν.
f_he 9 273·A.
牌f_nam 11 466·A.

  └ 正f_cmp_he(2) 正f_cmp_cl(3) 正f_cmp_rw(6) 正f_cmp_au(7) 正f_cmp_aw(9) 正f_cmp_cf(10) 正f_cmp_fr(11) [1.1K]
  └ f_he_or(5) [148]
  └ 牌f_nam_sc(8) [132]
  └ 册f_reg_di(6) [139]
**build/narrative/pigeon_compiler/runners** (9)
测编w_rct 7 156·Ν.
深划w_rdp 8 172·Ν.
鸽环f_rpl 9 295·Ν.
净拆f_rcs 10 300·W.
净助f_rcsh 11 183·Ν.
净初w_rcsi 12 241·Ν.
谱桥p_mbr 13 201·Ν.
复审p_rd 14 300·Ν.
批编f_rbc 15 232·R.

**build/narrative/pigeon_compiler/state_extractor** (6)
查p_ap 1 187·Ν.
演p_cg 2 225·Ν.
追p_it 3 184·Ν.
共态p_ssd 4 189·Ν.
阻w_ra 5 192·Ν.
拆f_emb 6 245·Ν.

**build/narrative/pigeon_compiler/weakness_planner** (1)
核w_dspp 4 358·D.

**build/narrative/src** (37)
时p_tu 1 104·Τ.
型p_mo 2 100·Π.
录p_lo 3 264·Ω.
境w_cb 4 182·Φ.
漂p_dw 5 268·18
桥p_rb 6 212·Π.
层w_sl 7 927·Π.
控f_ost 8 354·Ω.
控w_ops 8 370·W.
忆p_qm 10 265·18
叙p_pn 12 252·R.
思f_cr 14 336·18
推w_dp 17 314·B.
队p_tq 18 242·Q.
觉w_fc 19 461·18
变p_ms 21 184·18
补p_rwb 22 223·18
递p_sh 23 196·18
探p_ur 24 177·S.
环w_pc 25 359·S.
合p_us 26 267·F.
片w_sm 26 491·F.
路f_cxr 27 258·F.
声w_vs 28 333·F.
训w_trwr 28 334·F.
研w_rl 29 234·L.
警p_sa 30 303·V.
典w_sd 31 373·G.
编w_gc 32 415·G.
意w_is 34 351·C.

**build/narrative/src/cognitive** (10)
适p_ad 1 143·Ν.
隐p_un 2 233·Ν.
偏p_dr 3 342·Ν.

  └ 偏p_dr_bs(1) 偏p_dr_cb(2) 偏p_dr_dsd(3) 偏p_dr_bcc(4) [585]
  └ 隐p_un_he(1) 隐p_un_di(2) 隐p_un_or(3) [385]
**build/narrative/src/修_sf_s013** (11)
修f_sf_sh 1 121·H.
修f_sf_sqn 2 112·H.
修f_sf_sdd 3 119·H.
修f_sf_scfc 4 121·H.
修f_sf_sohc 5 126·H.
修f_sf_sde 6 118·H.
修f_sf_wr 7 136·H.
修f_sf_rsf 8 138·H.
修f_sf_aco 9 182·VR
修f_sf_sb 10 104·H.
修f_sf_aaif 11 141·H.

**build/narrative/src/忆_qm_s010** (6)
忆p_qm_co 1 106·H.
忆p_qm_fi 2 119·H.
忆p_qm_tu 3 118·H.
忆p_qm_cl 4 127·H.
忆p_qm_rq 5 140·H.
忆p_qm_lm 6 131·H.

**build/narrative/src/思_cr_s014** (12)
思f_cr_co 1 108·7.
思f_cr_so 2 121·7.
思f_cr_dp 3 129·7.
思f_cr_ch 4 125·7.
思f_cr_pg 5 135·7.
思f_cr_pb 6 112·7.
思f_cr_ac 7 111·7.
思f_cr_rc 8 126·7.
思f_cr_rl 9 112·7.
思f_cr_sfr 10 112·7.
思f_cr_pw 11 254·7.
思f_cr_dm 12 177·7.

**build/narrative/src/环_pc_s025** (8)
环w_pc_co 1 106·H.
环w_pc_lo 2 157·H.
环w_pc_se 3 132·H.
环w_pc_sy 4 113·H.
环w_pc_co 5 118·H.
环w_pc_mc 6 146·H.
环w_pc_pi 7 128·H.
环w_pc_or 8 149·H.

**build/narrative/src/管_cpm_s020** (10)
管w_cpm_co 1 95·7.
管w_cpm_bu 2 165·7.
管w_cpm_ju 3 123·7.
管w_cpm_op 4 144·7.
管w_cpm_ai 5 139·7.
管w_cpm_os 6 123·7.
管w_cpm_tu 7 140·7.
管w_cpm_au 8 116·7.
管w_cpm_in 9 162·7.
管w_cpm_or 10 138·G.

**build/narrative/src/觉_fc_s019** (12)
觉w_fc_he 1 146·H.
觉w_fc_pe 2 147·H.
觉w_fc_re 3 131·H.
觉w_fc_au 4 132·H.
觉w_fc_de 5 140·H.
觉w_fc_de 6 130·H.
觉w_fc_cl 7 114·H.
觉w_fc_pb 8 117·H.
觉w_fc_mo 9 134·H.
觉w_fc_da 10 129·H.
觉w_fc_dh 11 112·H.
觉w_fc_dw 12 128·H.

**build/narrative/streaming_layer** (19)
p_slc 1 92·Ν.
p_slsh 2 124·Ν.
p_sldc 4 150·Ν.
p_slf 4 202·Ν.
f_slcp 5 223·R.
p_sldc 5 113·Ν.
f_sla 6 224·R.
p_sldc 6 98·Ν.
w_slm 7 228·R.
f_slal 8 241·R.
p_slr 9 216·Ν.
p_sld 10 149·R.
w_slhh 11 225·R.
p_sldf 13 152·Ν.
p_sldy 13 117·Ν.
p_sldf 14 132·Ν.
p_slds 14 118·Ν.
f_slo 16 279·R.
f_slo 17 127·Ν.

**build/numerical/pigeon_brain/flow** (16)
算f_ps 14 3.2K·NU
虫f_bdm 15 2.2K·FT
读f_fi 16 1.7K·FT

  └ 存p_nm_co(1) 存p_nm_pu(2) 存p_nm_st(3) 存p_nm_di(4) 存p_nm_ph(5) 存p_nm_pr(6) 存p_nm_lh(7) 存p_nm_la(8) 存p_nm_pg(9) [1.1K]
  └ 预p_pr_co(1) 预p_pr_cu(2) 预p_pr_tr(5) 预p_pr_ss(6) [405]
**build/numerical/pigeon_compiler/rename_engine** (54)
追跑f_ruhe 10 3.3K·FX
册f_reg 12 1.5K·VR

  └ 正f_cmp_co(1) 正f_cmp_re(4) 正f_cmp_rh(5) 正f_cmp_ah(8) [381]
  └ f_he_rt(1) f_he_gf(2) f_he_ie(3) f_he_lw(4) [782]
  └ 谱建f_mb_co(1) 谱建f_mb_sl(2) 谱建f_mb_de(3) 谱建f_mb_se(4) 谱建f_mb_ee(5) 谱建f_mb_de(6) 谱建f_mb_ph(7) 谱建f_mb_sf(8) 谱建f_mb_se(9) 谱建f_mb_ce(10) 谱建f_mb_ce(11) 谱建f_mb_me(12) 谱建f_mb_fs(13) 谱建f_mb_si(14) 谱建f_mb_fp(15) 谱建f_mb_en(16) 谱建f_mb_fa(17) 谱建f_mb_dg(18) 谱建f_mb_ss(19) 谱建f_mb_cs(20) 谱建f_mb_pt(21) 谱建f_mb_ms(22) 谱建f_mb_bb(23) 谱建f_mb_hm(24) 谱建f_mb_cs(25) 谱建f_mb_hs(26) 谱建f_mb_kt(27) 谱建f_mb_st(28) 谱建f_mb_sm(29) 谱建f_mb_bm(30) 谱建f_mb_bam(31) [6.6K]
  └ 牌f_nam_co(1) 牌f_nam_do(2) 牌f_nam_sl(3) 牌f_nam_ex(4) 牌f_nam_bu(5) 牌f_nam_pa(6) 牌f_nam_de(7) [791]
  └ 册f_reg_co(1) 册f_reg_pu(2) 册f_reg_pa(3) 册f_reg_du(4) 册f_reg_vb(5) 册f_reg_br(7) [964]
**build/numerical/pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR** (13)
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_constants 1 122·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bug_utils 2 132·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_date_utils 3 41·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_io 4 192·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_filename_builders 5 170·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_parse_decomposed 6 291·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_mutate_compressed 7 122·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_builders 8 212·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bump_version 9 153·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_version_bump 9 299·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bump_all_versions 10 168·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_diff 11 103·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_orchestrator 12 13·OT

**build/numerical/pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc** (12)
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_constants 1 122·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bug_utils 2 111·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_date_utils 3 41·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_registry_io 4 171·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_filename_builders 5 151·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_parse_decomposed 6 240·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_mutate_compressed 7 122·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_registry_builders 8 212·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_version_bump 9 299·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bump_version 10 153·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bump_all_versions 11 168·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_diff_utils 12 103·OT

**build/numerical/pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc** (11)
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_git_commit 1 162·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_format_report 2 415·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_load_glyph 3 206·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_registry_stage 4 264·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_manifest_stage 5 129·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_compliance_stage 6 142·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_nametag_drift 7 440·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_rename_decomposed 8 562·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_glyph_drift_decomposed 9 881·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_main_orchestrator 10 293·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_run_heal_decomposed 11 555·OT

  └ 批编f_rbc_ma(1) 批编f_rbc_sc(2) 批编f_rbc_or(3) [1.3K]
**build/numerical/src** (22)
测p_rwd 9 958·P0
热p_fhm 11 2.1K·P0
修f_sf 13 3.9K·VR
脉p_ph 15 1.2K·P0
u_prc 16 2.1K·OT
u_pj 19 5.4K·NU
管w_cpm 20 1.4K·NU
u_pd 24 736·OT
u_pe 24 4.0K·P0
u_psg 26 467·OT
对p_tp 27 2.3K·VR
u_cs 33 1.1K·OT
虚f_mc 36 1.3K·OT

  └ .operator_stats_seq008_v010_d0331__persi_constants(1) .operator_stats_seq008_v010_d0331__persi_time_utils(2) .operator_stats_seq008_v010_d0331__persi_artifact_detection(3) .operator_stats_seq008_v010_d0331__persi_baselines(4) .operator_stats_seq008_v010_d0331__persi_classify_state(5) .operator_stats_seq008_v010_d0331__persi_timeframes(6) .operator_stats_seq008_v010_d0331__persi_observations(7) .operator_stats_seq008_v010_d0331__persi_markdown(8) .operator_stats_seq008_v010_d0331__persi_operator_stats(9) [3.1K]
**build/numerical/src/cognitive/drift** (6)
u_dbs 1 103·OT
u_dcbl 2 300·OT
u_ddsd 3 333·OT
u_ddsdh 4 9·OT
u_dbcc 5 491·OT
u_dbch 6 9·OT

**build/numerical/src/cognitive/unsaid** (8)
u_udd 1 111·OT
u_ucp 2 68·OT
u_ucdi 3 108·OT
u_uet 4 78·OT
u_uep 5 9·OT
u_usp 6 9·OT
u_uah 7 9·OT
u_uo 8 847·OT

**build/numerical/src/operator_stats** (13)
u_osct 1 31·OT
u_ostu 2 74·OT
u_oscl 3 212·OT
u_oscp 4 206·OT
u_osrr 5 152·OT
u_osrt 5 420·OT
u_osrd 6 171·OT
u_ostd 7 326·OT
u_ostf 7 326·OT
u_osro 8 666·OT
u_osrc 9 111·OT
u_osrf 10 152·OT
u_oscs 11 263·OT

**build/numerical/src/u_pe_s024_v002_d0402_λC** (13)
u_pe_s024_v002_d0402_λC_constants 1 59·OT
u_pe_s024_v002_d0402_λC_utils 2 136·OT
u_pe_s024_v002_d0402_λC_context_gatherers 3 846·OT
u_pe_s024_v002_d0402_λC_context_gatherers2 4 586·OT
u_pe_s024_v002_d0402_λC_context_gatherers3 5 400·OT
u_pe_s024_v002_d0402_λC_context_gatherers4 6 163·OT
u_pe_s024_v002_d0402_λC_prompt_builder 7 796·OT
u_pe_s024_v002_d0402_λC_enricher_core 8 453·OT
u_pe_s024_v002_d0402_λC_block_utils 9 256·OT
u_pe_s024_v002_d0402_λC_block_utils2 10 105·OT
u_pe_s024_v002_d0402_λC_injector 11 444·OT
u_pe_s024_v002_d0402_λC_injector_wrapper 12 444·OT
u_pe_s024_v002_d0402_λC_block_builder 13 13·OT

**build/numerical/src/u_pe_s024_v004_d0403_λP0_βoc** (10)
u_pe_s024_v004_d0403_λP0_βoc_constants 1 59·OT
u_pe_s024_v004_d0403_λP0_βoc_utils 2 136·OT
u_pe_s024_v004_d0403_λP0_βoc_data_loaders 3 846·OT
u_pe_s024_v004_d0403_λP0_βoc_bug_scoring 4 469·OT
u_pe_s024_v004_d0403_λP0_βoc_bug_routing 5 322·OT
u_pe_s024_v004_d0403_λP0_βoc_prompt_builder 6 806·OT
u_pe_s024_v004_d0403_λP0_βoc_enricher 7 464·OT
u_pe_s024_v004_d0403_λP0_βoc_block_utils 8 256·OT
u_pe_s024_v004_d0403_λP0_βoc_injector 9 338·OT
u_pe_s024_v004_d0403_λP0_βoc_main 10 13·OT

**build/numerical/src/u_pj_s019_v002_d0402_λC** (17)
u_pj_s019_v002_d0402_λC_constants 1 316·OT
u_pj_s019_v002_d0402_λC_utils 2 288·OT
u_pj_s019_v002_d0402_λC_text_processing 3 184·OT
u_pj_s019_v002_d0402_λC_composition_utils 4 203·OT
u_pj_s019_v002_d0402_λC_candidate_compositions 5 175·OT
u_pj_s019_v002_d0402_λC_select_composition 6 220·OT
u_pj_s019_v002_d0402_λC_intent_classification 7 157·OT
u_pj_s019_v002_d0402_λC_system_state 8 320·OT
u_pj_s019_v002_d0402_λC_coaching_utils 9 143·OT
u_pj_s019_v002_d0402_λC_running_stats_decomposed 10 415·OT
u_pj_s019_v002_d0402_λC_predict_next_issues_decomposed 11 494·OT
u_pj_s019_v002_d0402_λC_build_snapshot_decomposed 12 373·OT
u_pj_s019_v002_d0402_λC_snapshot_io 13 379·OT
u_pj_s019_v002_d0402_λC_write_snapshot 13 65·OT
u_pj_s019_v002_d0402_λC_refresh_copilot 14 336·OT
u_pj_s019_v002_d0402_λC_refresh_utils 15 249·OT
u_pj_s019_v002_d0402_λC_log_enriched_entry_decomposed 16 1.1K·OT

**build/numerical/src/修f_sf_s013_v012_d0402_初写谱净拆_λVR** (16)
修f_sf_s013_v012_d0402_初写谱净拆_λVR_constants 1 66·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_seq_base 2 82·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_hardcoded 3 259·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_dead_exports 4 473·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_duplicate_docstrings 5 207·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_cross_file_coupling 6 338·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_over_hard_cap 7 311·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_query_noise 8 171·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_compile_oversized 9 479·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_compile_helpers 10 13·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_write_self_fix_report 11 493·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_apply_import_fixes 12 690·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_import_processor 13 13·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_import_injector 14 13·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_run_self_fix 15 400·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_problem_collector 16 13·OT

**build/numerical/src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc** (12)
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_constants 1 66·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_seq_base 2 82·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_hardcoded 3 259·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_query_noise 4 171·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_dead_exports 5 473·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_duplicate_docstrings 6 207·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_cross_file_coupling 7 338·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_over_hard_cap 8 311·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_auto_compile_oversized 9 479·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_write_self_fix_report 10 493·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_auto_apply_import_fixes 11 716·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_run_self_fix 12 406·OT

**build/numerical/src/叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc** (7)
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_prompt_templates 1 13·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_load_composition 2 91·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_file_briefs 3 206·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_call_deepseek 4 183·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_narrative_subhelpers 5 13·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_narrative_wrapper 6 887·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_generate_narrative 7 271·OT

**build/numerical/src/对p_tp_s027_v003_d0402_缩分话_λVR_βoc** (6)
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_utils 1 319·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_intent_classifiers 2 307·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_matching 3 177·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_note_builders 4 169·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_capture_decomposed 5 512·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_summary_decomposed 6 800·OT

**build/numerical/src/控_ost_s008** (9)
控f_ost_co 1 33·OT
控f_ost_tu 2 67·OT
控f_ost_ad 3 85·OT
控f_ost_ba 4 231·OT
控f_ost_cs 5 400·OT
控f_ost_ti 6 355·OT
控f_ost_ob 7 687·OT
控f_ost_ma 8 683·OT
控f_ost_cl 9 473·OT

**build/numerical/src/推_dp_s017** (15)
推w_dp_ju 1 130·OT
推w_dp_gh 2 242·OT
推w_dp_pa 3 355·OT
推w_dp_ma 4 539·OT
推w_dp_maa 4 334·OT
推w_dp_mab 5 219·OT
推w_dp_da 6 484·OT
推w_dp_daa 6 404·OT
推w_dp_dab 7 92·OT
推w_dp_fc 8 402·OT
推w_dp_cc 9 198·OT
推w_dp_bch 10 9·OT
推w_dp_bcm 11 936·OT
推w_dp_ic 12 168·OT
推w_dp_ma 13 9·OT

**build/numerical/src/管_cpm_s020** (4)
管w_cpm_idx 12 2.1K·OT
管w_cpm_bvx 13 915·OT
管w_cpm_ops 14 1.3K·OT
管w_cpm_rmp 16 1.4K·OT

**build/numerical/src/管w_cpm_s020_v003_d0402_缩分话_λVR_βoc** (15)
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_constants 1 417·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_block_utils 2 193·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_file_utils 3 240·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_registry_utils 4 829·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_auto_index_decomposed 5 854·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_bug_voices 6 321·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_operator_state_decomposed 7 793·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_operator_state_helpers 8 13·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_audit_decomposed 9 552·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_refresh_decomposed 10 733·P0
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors 11 376·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_telemetry 12 198·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_voices_state 13 197·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_render 14 252·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_main 15 13·OT

**build/numerical/src/脉_ph_s015** (7)
脉p_ph_co 1 82·OT
脉p_ph_ut 2 80·OT
脉p_ph_in 3 232·OT
脉p_ph_rc 4 300·OT
脉p_ph_st 5 112·OT
脉p_ph_jo 6 96·OT
脉p_ph_or 7 341·OT

**build/numerical/src/警p_sa_s030_v003_d0402_缩分话_λV** (8)
警p_sa_s030_v003_d0402_缩分话_λV_constants 1 263·OT
警p_sa_s030_v003_d0402_缩分话_λV_parse_ts 2 60·OT
警p_sa_s030_v003_d0402_缩分话_λV_strip_alert 3 49·OT
警p_sa_s030_v003_d0402_缩分话_λV_extract_block 4 63·OT
警p_sa_s030_v003_d0402_缩分话_λV_check_staleness_helpers 5 13·OT
警p_sa_s030_v003_d0402_缩分话_λV_check_staleness 6 321·OT
警p_sa_s030_v003_d0402_缩分话_λV_inject_helpers 7 13·OT
警p_sa_s030_v003_d0402_缩分话_λV_inject_alert 8 346·OT

**client** (7)
推=chat_composition_analyzer 0 2.2K✓·OT
演=chat_response_reader 0 1.4K✓·OT
联=composition_recon 0 936✓·OT
OS=os_hook 0 2.4K✓·OT
telemetry_cleanup 0 391✓·OT
UI=uia_reader 0 1.0K✓·OT
VS=vscdb_poller 0 1.1K✓·OT

**pigeon_brain** (80)
规=__main__ 0 61✓·OT
录=_test_trace 0 163✓·OT
桥=ai_cognitive_log 0 1.1K✓·OT·hc
忆=build_narratives 0 308✓·OT
图=context_veins 0 1.7K✓·OT
GE=gemini_chat 0 2.1K✓·OT·hc
NO=node_tester 0 1.3K✓·OT·hc
pulse_tester 0 646✓·OT
令F=令f_cl_s009_v002_d0323_缩分话_λP 0 267✓·OT
仿F=仿f_dsm_s010_v002_d0323_缩分话_λP 0 417✓·OT
双F=双f_dsb_s008_v002_d0323_缩分话_λP 0 479✓·OT·oc
图p_ge_s003_v003_d0324_读唤任_λB 0 663✓·OT
图P=图p_ge_s003_v003_d0324_读唤任_λχ 0 663✓·OT·hc
型p_mo_s001_v002_d0323_读唤任_λP 0 204✓·OT
描P=描p_ghm_s004_v002_d0323_缩环检意_λP 0 326✓·OT·hc
服f_ls_s012_v003_d0324_踪稿析_λB 0 713✓·OT·oc
服f_ls_s012_v004_d0324_踪稿析_λB 0 788✓·OT·oc
服F=服f_ls_s012_v004_d0324_踪稿析_λδ 0 788✓·OT·oc
环检=环检p_ld_s005_v002_d0323_缩描意_λP 0 368✓·OT·hc
缩P=缩p_fdt_s006_v002_d0323_描环检意_λP 0 425✓·OT·hc
观F=观f_os_s007_v003_d0401_读谱建册_λA 0 457✓·OT
读W=读w_el_s002_v003_d0401_观话_λA 0 560✓·OT
跑F=跑f_tr_s013_v002_d0323_缩分话_λP 0 334✓·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP 0 392✓·OT·hc

**pigeon_brain/flow** (79)
引=_resolve 0 345✓·OT
任W=任w_tawr_s005_v003_d0401_唤脉运分_λA 0 563✓·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR 0 526✓·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR 0 530✓·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ 0 530✓·OT
包P=包p_cpk_s001_v002_d0324_缩分话_λε 0 434✓·OT·hc
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA 0 493✓·OT
存p_nm_s008_v001_d0325_读唤任_λB 0 791✓·OT·oc
存p_nm_s008_v003_d0328_读唤任_λR 0 791✓·OT·oc
学f_ll_s013_v003_d0327_读唤任_λS 0 976✓·OT·oc
择P=择p_pase_s004_v002_d0324_分话唤_λε 0 595✓·OT
流F=流f_fe_s003_v002_d0324_缩分话_λε 0 555✓·OT
算f_ps_s014_v006_d0404_译改名踪_λNU_βoc 0 2.2K✓·OT·oc
结U=结u_fxs_s011_v001_d0325_λB 0 557✓·OT
脉运=脉运w_vt_s006_v003_d0401_唤分话_λA 0 413✓·OT
话f_nc_s012_v002_d0328_读唤脉运_λR 0 567✓·OT
话F=话f_nc_s012_v004_d0328_读唤脉运_λR 0 567✓·OT
逆f_ba_s007_v002_d0328_踪稿析_λR 0 980✓·OT·oc
逆f_ba_s007_v005_d0404_踪稿析_λNU_βoc 0 951✓·OT·oc
预p_pr_s009_v002_d0328_踪稿析_λR 0 817✓·OT·oc
预p_pr_s009_v003_d0327_踪稿析_λS 0 681✓·OT
预p_pr_s009_v003_d0330_踪稿析_λF 0 938✓·OT·oc
预p_pr_s009_v004_d0330_踪稿析_λρ 0 938✓·OT·oc

**pigeon_brain/flow/_resolve** (3)
引=_resolve_pb_import 1 161·OT
引=_resolve_find_module 2 530·OT
引=_resolve_flow_import 3 303·OT

  └ 逆f_ba_bp_s005_v003_d0328_λR(0) 逆f_ba_bp_s005_v004_d0327_λγ(0) 逆f_ba_da_s004_v003_d0328_λR(0) 逆f_ba_da_s004_v004_d0327_λγ(0) 逆f_ba_fl_s001_v002_d0327_λS(0) 逆f_ba_lc_s002_v002_d0327_λS(0) 逆f_ba_to_s003_v002_d0327_λS(0) [1.5K]
  └ 学f_ll_cu_s006_v003_d0327_λγ(0) 学f_ll_cu_s006_v003_d0328_λR(0) 学f_ll_jl_s002_v002_d0327_λS(0) 学f_ll_lh_s007_v002_d0327_λS(0) 学f_ll_ml_s008_v003_d0327_λγ(0) 学f_ll_ml_s008_v003_d0328_λR(0) 学f_ll_pc_s003_v003_d0328_λR(0) 学f_ll_pc_s003_v004_d0327_λγ(0) 学f_ll_pc_s003_v004_d0328_λR(0) 学f_ll_sc_s005_v003_d0328_λR(0) 学f_ll_sc_s005_v004_d0327_λγ(0) 学f_ll_sc_s005_v004_d0328_λR(0) 学f_ll_sch_s004_v002_d0327_λS(0) 学f_ll_su_s001_v002_d0327_λS(0) [2.3K]
  └ 存p_nm_co_s001_v001(0) 存p_nm_di_s004_v001(0) 存p_nm_la_s008_v001(0) 存p_nm_lh_s007_v001(0) 存p_nm_pg_s009_v001(0) 存p_nm_ph_s005_v001(0) 存p_nm_pr_s006_v001(0) 存p_nm_pu_s002_v001(0) 存p_nm_st_s003_v001(0) [795]
  └ 算f_ps_ca_s009_v002_d0327_λS(0) 算f_ps_co_s001_v002_d0327_λS(0) 算f_ps_dl_s003_v002_d0327_λS(0) 算f_ps_esa_s006_v002_d0327_λS(0) 算f_ps_me_s005_v002_d0327_λS(0) 算f_ps_nb_s010_v003_d0328_λR(0) 算f_ps_nb_s010_v004_d0327_λγ(0) 算f_ps_pcs_s012_v003_d0328_λR(0) 算f_ps_pcs_s012_v004_d0327_λγ(0) 算f_ps_pes_s011_v003_d0328_λR(0) 算f_ps_pes_s011_v004_d0327_λγ(0) 算f_ps_pu_s002_v002_d0327_λS(0) 算f_ps_rl_s004_v002_d0327_λS(0) 算f_ps_rm_s007_v002_d0327_λS(0) 算f_ps_sc_s008_v002_d0327_λS(0) 算f_ps_si_s003_v002_d0327_λS(0) [2.4K]
  └ 预p_pr_co_s001_v001(0) 预p_pr_co_s003_v001(0) 预p_pr_co_s003_v002_d0330_λρ(0) 预p_pr_cu_s002_v001(0) 预p_pr_pr_s007_v001(0) 预p_pr_pr_s007_v002_d0330_λρ(0) 预p_pr_ss_s006_v001(0) 预p_pr_te_s004_v001(0) 预p_pr_te_s004_v002_d0330_λρ(0) 预p_pr_tr_s005_v001(0) [1.7K]
**pigeon_brain/flow/分f_dvp_s010_v002_d0328_唤脉运观_λR** (7)
分f_dvp_s010_v002_d0328_唤脉运观_λR_plan_path 1 60·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_node_performance 2 27·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_training_needs 3 26·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_fix_patterns 4 26·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_cognitive_trend 5 26·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_predictions 6 25·OT
分f_dvp_s010_v002_d0328_唤脉运观_λR_orchestrator 7 1.2K·OT

**pigeon_brain/flow/分f_dvp_s010_v003_d0328_唤脉运观_λR** (7)
分f_dvp_s010_v003_d0328_唤脉运观_λR_plan_path 1 60·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_node_performance 2 27·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_training_needs 3 26·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_fix_patterns 4 26·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_cognitive_trend 5 26·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_predictions 6 25·OT
分f_dvp_s010_v003_d0328_唤脉运观_λR_orchestrator 7 1.2K·OT

**pigeon_brain/flow/分f_dvp_s010_v004_d0327_唤脉运观_λγ** (6)
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_plan_path 1 60·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_section_nodes 2 26·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_section_fixes 3 26·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_section_trend 4 26·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_section_predictions 5 27·OT
分F=分f_dvp_s010_v004_d0327_唤脉运观_λγ_orchestrator 6 1.2K·OT

**pigeon_brain/flow/包p_cpk_s001_v002_d0324_缩分话_λε** (4)
包P=包p_cpk_s001_v002_d0324_缩分话_λε_constants 1 40·OT
包P=包p_cpk_s001_v002_d0324_缩分话_λε_node_intel 2 186·OT
包P=包p_cpk_s001_v002_d0324_缩分话_λε_context_packet 3 628·OT
包P=包p_cpk_s001_v002_d0324_缩分话_λε_factory 4 89·OT

**pigeon_brain/flow/唤w_noaw_s002_v003_d0401_脉运分话_λA** (5)
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA_constants 1 69·OT
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA_tokenize 2 116·OT
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA_compute_relevance 3 327·OT
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA_awaken_helpers 4 26·OT
唤W=唤w_noaw_s002_v003_d0401_脉运分话_λA_awaken_orchestrator 5 569·OT

**pigeon_brain/flow/脉运w_vt_s006_v003_d0401_唤分话_λA** (4)
脉运=脉运w_vt_s006_v003_d0401_唤分话_λA_constants 1 52·OT
脉运=脉运w_vt_s006_v003_d0401_唤分话_λA_helpers 2 170·OT
脉运=脉运w_vt_s006_v003_d0401_唤分话_λA_edge_health 3 308·OT
脉运=脉运w_vt_s006_v003_d0401_唤分话_λA_transport 4 304·OT

**pigeon_brain/flow/虫f_bdm_s015_v001_d0410_λFT** (15)
虫f_bdm_s015_v001_d0410_λFT_constants 1 186·OT
虫f_bdm_s015_v001_d0410_λFT_bugmanifest 2 182·OT
虫f_bdm_s015_v001_d0410_λFT_loaders 3 336·OT
虫f_bdm_s015_v001_d0410_λFT_graph_utils 4 336·OT
虫f_bdm_s015_v001_d0410_λFT_bug_loader 5 476·OT
虫f_bdm_s015_v001_d0410_λFT_bug_loader_decomposed 5 479·OT
虫f_bdm_s015_v001_d0410_λFT_propagate 6 467·OT
虫f_bdm_s015_v001_d0410_λFT_propagate_decomposed 6 469·OT
虫f_bdm_s015_v001_d0410_λFT_inject 7 334·OT
虫f_bdm_s015_v001_d0410_λFT_write_memory 8 517·OT
虫f_bdm_s015_v001_d0410_λFT_write_memory_decomposed 8 520·OT
虫f_bdm_s015_v001_d0410_λFT_log 9 106·OT
虫f_bdm_s015_v001_d0410_λFT_orchestrator 10 409·OT
虫f_bdm_s015_v001_d0410_λFT_demo 11 886·OT
虫f_bdm_s015_v001_d0410_λFT_demo_decomposed 11 889·OT

**pigeon_brain/flow/读f_fi_s016_v001_d0410_λFT** (9)
读f_fi_s016_v001_d0410_λFT_constants 1 155·OT
读f_fi_s016_v001_d0410_λFT_gemini_calls 2 345·OT
读f_fi_s016_v001_d0410_λFT_node_memory 3 262·OT
读f_fi_s016_v001_d0410_λFT_parsing 4 252·OT
读f_fi_s016_v001_d0410_λFT_prompt_builder 5 297·OT
读f_fi_s016_v001_d0410_λFT_priority 6 87·OT
读f_fi_s016_v001_d0410_λFT_interrogation_core 7 420·OT
读f_fi_s016_v001_d0410_λFT_sweep 8 407·OT
读f_fi_s016_v001_d0410_λFT_briefing 9 246·OT

**pigeon_brain/仿f_dsm_s010_v002_d0323_缩分话_λP** (3)
仿F=仿f_dsm_s010_v002_d0323_缩分话_λP_constants 1 80·OT
仿F=仿f_dsm_s010_v002_d0323_缩分话_λP_sim_helpers 2 25·OT
仿F=仿f_dsm_s010_v002_d0323_缩分话_λP_main 3 1.1K·OT

**pigeon_brain/双f_dsb_s008_v002_d0323_缩分话_λP** (4)
双F=双f_dsb_s008_v002_d0323_缩分话_λP_utils 1 332·OT
双F=双f_dsb_s008_v002_d0323_缩分话_λP_node_builder 2 25·OT
双F=双f_dsb_s008_v002_d0323_缩分话_λP_orchestrator 3 835·OT
双F=双f_dsb_s008_v002_d0323_缩分话_λP_renderer 4 121·OT

**pigeon_brain/型p_mo_s001_v002_d0323_读唤任_λP** (6)
型p_mo_s001_v002_d0323_读唤任_λP_constants 1 35·OT
型p_mo_s001_v002_d0323_读唤任_λP_event_type 2 67·OT
型p_mo_s001_v002_d0323_读唤任_λP_electron_status 3 80·OT
型p_mo_s001_v002_d0323_读唤任_λP_death_cause 4 72·OT
型p_mo_s001_v002_d0323_读唤任_λP_execution_event 5 128·OT
型p_mo_s001_v002_d0323_读唤任_λP_electron 6 165·OT

**pigeon_brain/描p_ghm_s004_v002_d0323_缩环检意_λP** (3)
描P=描p_ghm_s004_v002_d0323_缩环检意_λP_constants 0 49·OT
描P=描p_ghm_s004_v002_d0323_缩环检意_λP_load 1 389·OT
描P=描p_ghm_s004_v002_d0323_缩环检意_λP_update 2 406·OT

**pigeon_brain/环检p_ld_s005_v002_d0323_缩描意_λP** (4)
环检=环检p_ld_s005_v002_d0323_缩描意_λP_constants 1 45·OT
环检=环检p_ld_s005_v002_d0323_缩描意_λP_fingerprint 2 92·OT
环检=环检p_ld_s005_v002_d0323_缩描意_λP_load_stats 3 412·OT
环检=环检p_ld_s005_v002_d0323_缩描意_λP_record_path 4 385·OT

**pigeon_brain/缩p_fdt_s006_v002_d0323_描环检意_λP** (4)
缩P=缩p_fdt_s006_v002_d0323_描环检意_λP_constants 1 53·OT
缩P=缩p_fdt_s006_v002_d0323_描环检意_λP_record 2 187·OT
缩P=缩p_fdt_s006_v002_d0323_描环检意_λP_stats 3 341·OT
缩P=缩p_fdt_s006_v002_d0323_描环检意_λP_classify 4 424·OT

**pigeon_brain/观f_os_s007_v003_d0401_读谱建册_λA** (6)
观F=观f_os_s007_v003_d0401_读谱建册_λA_constants 1 33·OT
观F=观f_os_s007_v003_d0401_读谱建册_λA_load_human_heat 2 188·OT
观F=观f_os_s007_v003_d0401_读谱建册_λA_build_prompt_helpers 3 27·OT
观F=观f_os_s007_v003_d0401_读谱建册_λA_build_prompt_wrapper 4 630·OT
观F=观f_os_s007_v003_d0401_读谱建册_λA_write_coaching 5 103·OT
观F=观f_os_s007_v003_d0401_读谱建册_λA_synthesize 6 414·OT

**pigeon_brain/跑f_tr_s013_v002_d0323_缩分话_λP** (4)
跑F=跑f_tr_s013_v002_d0323_缩分话_λP_ws_push 1 24·OT
跑F=跑f_tr_s013_v002_d0323_缩分话_λP_exec_script 2 25·OT
跑F=跑f_tr_s013_v002_d0323_缩分话_λP_report_results 3 26·OT
跑F=跑f_tr_s013_v002_d0323_缩分话_λP_main 4 687·OT

**pigeon_brain/钩w_th_s011_v002_d0323_缩分话_λP** (6)
钩W=钩w_th_s011_v002_d0323_缩分话_λP_shared_state 1 25·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP_build_module_map 2 185·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP_trace_helpers 3 25·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP_trace_fn 4 403·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP_buffer_ops 5 130·OT
钩W=钩w_th_s011_v002_d0323_缩分话_λP_trace_control 6 152·OT

**pigeon_compiler** (71)
GI=git_plugin 0 6.0K~·OT·oc
PI=pigeon_limits 0 348✓·OT·hc
pre_commit_audit 0 945✓·OT·oc
SE=session_logger 0 295✓·OT

**pigeon_compiler/cut_executor** (12)
写W=写w_fw_s003_v005_d0322_译改名踪_λμ 0 307✓·OT
切P=切p_ss_s002_v004_d0315_重箱重助重拆_λν 0 189✓·OT·hc
初写=初写p_iw_s007_v007_d0322_净拆译_λ7 0 131✓·OT
析P=析p_pp_s001_v004_d0315_测编深划鸽环_λν 0 142✓·OT
稿P=稿p_mw_s005_v004_d0315_册追跑谱桥_λν 0 183✓·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7 0 757✓·OT
译F=译f_fdc_s008_v005_d0322_净拆测编深划_λ7 0 260✓·OT
踪P=踪p_if_s004_v004_d0315_牌册谱桥_λν 0 166✓·OT
重助=重助p_rehe_s011_v004_d0315_重箱重拆切_λν 0 195✓·OT·hc
重拆=重拆f_res_s009_v004_d0315_重箱谱建织_λν 0 345✓·OT
重箱=重箱f_rebi_s010_v004_d0315_重拆谱建织_λν 0 262✓·OT
验W=验w_pv_s006_v004_d0315_重箱重拆追跑_λν 0 221✓·OT

**pigeon_compiler/cut_executor/织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7** (8)
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_strip_duplicates 1 587·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_strip_helpers 2 26·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_strip_wrapper 3 587·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_find_classes 4 99·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_prompt_builder 5 535·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_deepseek_call 6 157·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_orchestrator 7 550·OT
织F=织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_replacement_logic 8 27·OT

**pigeon_compiler/git_plugin** (49)
GI=git_plugin_constants 1 284·OT
GI=git_plugin_helpers 2 415·OT
GI=git_plugin_utils 2 532·OT
p_gph 2 479·GI
GI=git_plugin_git_helpers 3 256·OT
GI=git_plugin_git_ops 3 255·OT
GI=git_plugin_intent_parsing 4 224·OT
p_gpip 4 436·GI
GI=git_plugin_bug_metadata 5 526·OT
GI=git_plugin_prompt_box 6 369·OT
GI=git_plugin_copilot_index 7 567·OT
GI=git_plugin_operator_profile 8 433·OT
GI=git_plugin_coaching_prose 9 159·OT
GI=git_plugin_operator_history 9 160·OT
GI=git_plugin_registry_churn 10 142·OT
GI=git_plugin_deep_signals 11 808·OT
GI=git_plugin_deepseek_api 12 244·OT
GI=git_plugin_commit_coaching_prompt 13 1.3K·OT
GI=git_plugin_edit_tracking 13 351·OT
GI=git_plugin_coaching_prompt 14 1.3K·OT
GI=git_plugin_generate_coaching 14 1.2K·OT
GI=git_plugin_coaching_generator 15 1.2K·OT
GI=git_plugin_refresh_operator_state 15 910·OT
GI=git_plugin_edit_data 16 350·OT
GI=git_plugin_operator_state 16 908·OT
GI=git_plugin_post_commit 17 2.1K·OT
GI=git_plugin_post_commit_extras 17 61·OT
GI=git_plugin_process_changed_files 18 1.3K·OT
GI=git_plugin_main_orchestrator 19 5.8K·OT
GI=git_plugin_run_helpers 19 605·OT
GI=git_plugin_run_helpers_a 19 385·OT
w_gpmo 19 7.0K·GI·oc
GI=git_plugin_run_helpers_b 20 243·OT
GI=git_plugin_import_rewrite 21 281·OT
GI=git_plugin_rename_ops 21 682·OT
GI=git_plugin_file_rename 22 342·OT
GI=git_plugin_log_inject 23 180·OT
GI=git_plugin_self_fix 24 605·OT
GI=git_plugin_bug_marker 25 490·OT
GI=git_plugin_module_calls 25 2.4K·OT
GI=git_plugin_module_calls 26 341·OT
GI=git_plugin_tc_trajectory 26 370·OT
GI=git_plugin_pulse_harvest 27 165·OT
GI=git_plugin_interlink 28 379·OT
GI=git_plugin_prompt_manager 29 248·OT
GI=git_plugin_compression 30 505·OT
GI=git_plugin_vitals 31 181·OT
GI=git_plugin_manifest_rebuild 32 151·OT
GI=git_plugin_orchestrator 33 661·OT

**pigeon_compiler/integrations** (1)
谱P=谱p_dsa_s001_v006_d0322_读_λ7 0 362✓·OT·hc

**pigeon_compiler/rename_engine** (76)
追=f_he_s009_v005_d0401_改名册追跑_λA 0 772✓·OT
p_ex_s004_v004_d0315_册追跑复审_λν 0 251✓·OT·hc
w_pl_s002_v005_d0401_册追跑谱桥_λA 0 463✓·OT·hc
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc 0 1.2K✓·OT·oc
审P=审p_va_s005_v005_d0403_踪稿析_λFX 0 354✓·OT·hc
引W=引w_ir_s003_v005_d0403_踪稿析_λFX 0 735✓·OT·oc+hc
扫P=扫p_sc_s001_v004_d0315_踪稿析_λν 0 336✓·OT·hc
改名=改名f_rr_s006_v005_d0401_追跑拆谱建_λA 0 437✓·OT
正F=正f_cmp_s008_v004_d0315_踪稿析_λν 0 616✓·OT·oc+hc
牌f_nam_s011_v004_d0401_追谱建踪_λA 0 1.6K✓·OT·oc+hc
谱建f_mb_s007_v003_d0314_观重箱重拆_λD 0 3.6K~·OT·oc+hc
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc 0 1.4K✓·OT·oc

  └ 正f_cmp_ah_s008_v001(0) 正f_cmp_au_s007_v004_d0322_λ7(0) 正f_cmp_aw_s009_v004_d0322_λ7(0) 正f_cmp_cf_s010_v004_d0322_λ7(0) 正f_cmp_cl_s003_v004_d0322_λ7(0) 正f_cmp_co_s001_v001(0) 正f_cmp_fr_s011_v004_d0322_λ7(0) 正f_cmp_he_s002_v004_d0322_λ7(0) 正f_cmp_re_s004_v001(0) 正f_cmp_rh_s005_v001(0) 正f_cmp_rw_s006_v004_d0322_λ7(0) [1.1K]
**pigeon_compiler/rename_engine/f_he_s009_v005_d0401_改名册追跑_λA** (5)
追=f_he_s009_v005_d0401_改名册追跑_λA_heal_report 1 377·OT
追=f_he_s009_v005_d0401_改名册追跑_λA_git_utils 2 359·OT
追=f_he_s009_v005_d0401_改名册追跑_λA_intent_extract 3 254·OT
追=f_he_s009_v005_d0401_改名册追跑_λA_logging 4 190·OT
追=f_he_s009_v005_d0401_改名册追跑_λA_heal_core 5 699·OT

  └ f_he_gf_s002_v001(0) f_he_ie_s003_v001(0) f_he_lw_s004_v001(0) f_he_or_s005_v002_d0401_λA(0) f_he_rt_s001_v001(0) [698]
  └ 谱建f_mb_bam_s031_v001(0) 谱建f_mb_bb_s023_v001(0) 谱建f_mb_bm_s030_v001(0) 谱建f_mb_ce_s010_v001(0) 谱建f_mb_ce_s011_v001(0) 谱建f_mb_co_s001_v001(0) 谱建f_mb_cs_s020_v001(0) 谱建f_mb_cs_s025_v001(0) 谱建f_mb_de_s003_v001(0) 谱建f_mb_de_s006_v001(0) 谱建f_mb_dg_s018_v001(0) 谱建f_mb_ee_s005_v001(0) 谱建f_mb_en_s016_v001(0) 谱建f_mb_fa_s017_v001(0) 谱建f_mb_fp_s015_v001(0) 谱建f_mb_fs_s013_v001(0) 谱建f_mb_hm_s024_v001(0) 谱建f_mb_hs_s026_v001(0) 谱建f_mb_kt_s027_v001(0) 谱建f_mb_me_s012_v001(0) 谱建f_mb_ms_s022_v001(0) 谱建f_mb_ph_s007_v001(0) 谱建f_mb_pt_s021_v001(0) 谱建f_mb_se_s004_v001(0) 谱建f_mb_se_s009_v001(0) 谱建f_mb_sf_s008_v001(0) 谱建f_mb_si_s014_v001(0) 谱建f_mb_sl_s002_v001(0) 谱建f_mb_sm_s029_v001(0) 谱建f_mb_ss_s019_v001(0) 谱建f_mb_st_s028_v001(0) [3.9K]
  └ 牌f_nam_bu_s005_v001(0) 牌f_nam_co_s001_v001(0) 牌f_nam_de_s007_v001(0) 牌f_nam_do_s002_v001(0) 牌f_nam_ex_s004_v001(0) 牌f_nam_pa_s006_v001(0) 牌f_nam_sc_s008_v002_d0401_λA(0) 牌f_nam_sl_s003_v001(0) [741]
  └ bump_all_versions_seq005b_v001(0) bump_version_seq005a_v001(0) 册f_reg_br_s007_v001(0) 册f_reg_co_s001_v001(0) 册f_reg_di_s006_v002_d0401_λA(0) 册f_reg_du_s004_v001(0) 册f_reg_pa_s003_v001(0) 册f_reg_pu_s002_v001(0) 册f_reg_vb_s005_v001(0) [996]
**pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR** (13)
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bug_utils_seq002_v001 0 114✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bump_all_versions_seq010_v001 0 121✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_bump_version_seq009_v001 0 123✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_constants_seq001_v001 0 49✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_date_utils_seq003_v001 0 25✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_diff_seq011_v001 0 69✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_filename_builders_seq005_v001 0 140✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_mutate_compressed_seq007_v001 0 119✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_orchestrator_seq012_v001 0 6✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_parse_decomposed_seq006_v001 0 186✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_builders_seq008_v001 0 128✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_io_seq004_v001 0 98✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_version_bump_seq009_v001 0 232✓·OT

**pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc** (12)
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bug_utils_seq002_v001 0 110✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bump_all_versions_seq011_v001 0 121✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bump_version_seq010_v001 0 123✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_constants_seq001_v001 0 49✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_date_utils_seq003_v001 0 25✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_diff_utils_seq012_v001 0 69✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_filename_builders_seq005_v001 0 136✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_mutate_compressed_seq007_v001 0 119✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_parse_decomposed_seq006_v001 0 176✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_registry_builders_seq008_v001 0 128✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_registry_io_seq004_v001 0 94✓·OT
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_version_bump_seq009_v001 0 232✓·OT

**pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX** (7)
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_constants 1 388·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_extract_top_module 2 163·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_replace_exact_module_path 3 101·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_rewrite_line 4 562·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_utility_helpers 5 241·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_rewrite_file 6 131·OT
引W=引w_ir_s003_v005_d0403_踪稿析_λFX_orchestrator 7 458·OT

**pigeon_compiler/rename_engine/谱建f_mb_s007_v003_d0314_观重箱重拆_λD** (36)
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_constants 1 378·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_docstring 2 284·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_scan_extract 2 1.8K·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_seq 3 70·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_exports 4 252·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_deps 5 231·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_parse_pigeon_header 6 314·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_signatures 7 588·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_format_signature 7 373·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_signatures_only 8 247·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_classes 9 302·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_constants 10 219·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_markers 11 151·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_scan_folder 12 344·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_sections 13 1.7K·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_signatures_constants 13 439·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_pigeon_markers 14 412·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_folder_api 15 529·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_folder_api_only 15 350·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_dep_graph 16 215·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_status_purpose 17 245·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_utils 17 429·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_parse_notes 18 220·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_should_skip 19 92·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_all_manifests 20 308·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_sync_master_decomposed 21 615·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_sync_master_wrapper 21 614·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_structure_tree 22 714·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_keystroke_trail 23 1.1K·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_find_bursts 24 223·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_keystroke_helpers 24 854·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_load_hesitation_map 25 202·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_hesitation_only 26 344·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_hesitation_summary 26 497·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_classify_state 27 180·OT
谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_manifest_decomposed 28 1.2K·OT

**pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc** (11)
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_compliance_stage_seq006_v001 0 59✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_format_report_seq002_v001 0 166✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_git_commit_seq001_v001 0 97✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_glyph_drift_decomposed_seq009_v001 0 301✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_load_glyph_seq003_v001 0 106✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_main_orchestrator_seq010_v001 0 109✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_manifest_stage_seq005_v001 0 71✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_nametag_drift_seq007_v001 0 184✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_registry_stage_seq004_v001 0 126✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_rename_decomposed_seq008_v001 0 204✓·OT
追跑=追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_run_heal_decomposed_seq011_v001 0 236✓·OT

**pigeon_compiler/runners** (12)
净初=净初w_rcsi_s012_v004_d0315_追跑净助鸽环_λν 0 654✓·OT
净助=净助f_rcsh_s011_v004_d0315_追跑净初鸽环_λν 0 167✓·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW 0 786✓·OT·oc+hc
复审=复审p_rd_s014_v004_d0315_册追跑观_λν 0 601✓·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR 0 718✓·OT·oc
测编=测编w_rct_s007_v004_d0315_深划鸽环译_λν 0 189✓·OT
深划=深划w_rdp_s008_v004_d0315_测编鸽环译_λν 0 196✓·OT
谱桥=谱桥p_mbr_s013_v004_d0315_册谱建环检_λν 0 405✓·OT
鸽环=鸽环f_rpl_s009_v004_d0315_追跑净助净初_λν 0 908✓·OT·oc

  └ 批编f_rbc_ma_s001_v001(0) 批编f_rbc_or_s003_v001(0) 批编f_rbc_sc_s002_v001(0) [653]
**pigeon_compiler/runners/净拆f_rcs_s010_v006_d0322_译测编深划_λW** (11)
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_constants 1 62·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_load_plan 2 139·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_next_seq 3 116·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_main 4 267·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase1 5 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase2 6 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase3 7 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase4 8 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase5 9 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_phase6 10 26·OT
净拆=净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_orchestrator 11 1.7K·OT

**pigeon_compiler/runners/批编f_rbc_s015_v002_d0328_织谱建验_λR** (6)
批编f_rbc_s015_v002_d0328_织谱建验_λR_constants 1 143·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR_scanner 2 444·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR_scanner_core 3 26·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR_batch_core 4 25·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR_orchestrator 5 1.0K·OT
批编f_rbc_s015_v002_d0328_织谱建验_λR_main 6 207·OT

**pigeon_compiler/state_extractor** (6)
共态=共态p_ssd_s004_v004_d0315_重箱重助重拆_λν 0 219✓·OT
拆F=拆f_emb_s006_v004_d0315_追跑改名谱建_λν 0 188✓·OT
查P=查p_ap_s001_v004_d0315_重箱重助重拆_λν 0 243✓·OT
演P=演p_cg_s002_v004_d0315_重箱重助重拆_λν 0 367✓·OT
追P=追p_it_s003_v004_d0315_牌谱建踪_λν 0 283✓·OT
阻W=阻w_ra_s005_v004_d0315_重箱重助重拆_λν 0 407✓·OT

**pigeon_compiler/weakness_planner** (1)
核W=核w_dspp_s004_v003_d0314_测编深划鸽环_λD 0 1.3K✓·OT·oc

**src** (142)
查=bug_profiles 0 1.4K✓·OT
层=codebase_detector 0 519✓·OT
控=codebase_transmuter 0 2.3K✓·OT
织=codebase_vitals 0 842✓·OT
脉=context_compressor 0 439✓·OT
审=copilot_prompt_manager_seq020_v003_d0402__compatibility_wrapper_for_the_legacy_lc_restore_rename_safe 0 93✓·OT
写=engagement_hooks 0 2.7K✓·OT
读=entropy_shedding 0 1.3K✓·OT·hc
压=escalation_engine 0 3.0K✓·OT
FI=file_selector 0 849✓·OT
IN=intent_compressor 0 1.6K✓·OT
MO=module_identity 0 3.8K~·OT
NA=narrative_glove 0 853✓·OT
NU=numeric_surface 0 710✓·OT
OP=operator_probes 0 1.2K✓·OT
PE=persona_intent_synthesizer 0 592✓·OT
pre_query_engine 0 1.2K✓·OT
profile_chat_server 0 2.2K✓·OT
profile_renderer 0 3.3K~·OT
prompt_enricher_seq024_v001 0 1.7K✓·OT
prompt_journal_seq019_v001 0 111✓·OT
prompt_recon_seq016_v001 0 133✓·OT·hc
PR=prompt_signal_seq026_v001 0 156✓·OT
PU=push_snapshot 0 2.2K✓·OT
SC=scale_inference 0 726✓·OT
self_fix_tracker 0 1.0K✓·OT
tc_buffer_watcher 0 193✓·OT
tc_constants 0 74✓·OT
tc_context 0 711✓·OT
tc_context_agent 0 1.2K✓·OT
tc_gemini 0 1.9K✓·OT
tc_popup 0 1.5K✓·OT
tc_profile 0 2.9K✓·OT
tc_sim 0 3.2K~·OT
tc_vscode 0 151✓·OT
TC=tc_web 0 264✓·OT
TE=template_selector 0 2.1K✓·OT
TH=thought_completer 0 214✓·OT
u_cs_s033_v001 0 843✓·OT·oc+hc
u_pd_s024_v001 0 491✓·OT
u_pe_s024_v004_d0403_λP0_βoc 0 2.2K✓·OT·oc
u_pj_s019_v003_d0404_λNU_βoc 0 2.9K✓·OT·oc
u_prc_s016_v001 0 985✓·OT·oc
u_psg_s026_v001 0 349✓·OT
UN=unsaid_accumulator 0 309✓·OT
VI=vitals_renderer 0 1.1K✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc 0 2.1K✓·OT·oc
典W=典w_sd_s031_v002_d0401_缩分话_λG 0 1.9K✓·OT·oc+hc
变P=变p_ms_s021_v002_d0321_缩分话_λ18 0 602✓·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR 0 796✓·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0 0 796✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc 0 869✓·OT
合P=合p_us_s026_v002_d0330_缩分话_λF 0 794✓·OT·oc
型P=型p_mo_s002_v003_d0317_读唤任_λΠ 0 131✓·OT
境W=境w_cb_s004_v008_d0321_初写谱净拆_λφ 0 258✓·OT
声W=声w_vs_s028_v002_d0330_缩分话_λF 0 2.2K✓·OT·oc
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc 0 1.3K✓·OT·oc
层W=层w_sl_s007_v003_d0317_读唤任_λΠ 0 3.1K~·OT·oc
录P=录p_lo_s003_v005_d0322_译改名踪_λω 0 471✓·OT
忆p_qm_s010_v004_d0321_踪稿析_λ18 0 861✓·OT
思f_cr_s014_v003_d0321_译改名踪_λ18 0 2.0K✓·OT·oc
思f_cr_s014_v004_d0330_译改名踪_λF 0 2.1K✓·OT·oc
思f_cr_s014_v005_d0331_译改名踪_λM 0 2.1K✓·OT·oc
意W=意w_is_s034_v002_d0401_缩分话_λC 0 2.2K✓·OT·oc
探p_ur_s024_v002_d0329_读唤任_λS 0 514✓·OT
探P=探p_ur_s024_v003_d0331_读唤任_λI 0 719✓·OT
控f_ost_s008_v007_d0322_初写谱净拆_λω 0 2.3K✓·OT·oc
控w_ops_s008_v007_d0322_册追跑_λW 0 2.1K✓·OT·oc
控w_ops_s008_v008_d0331_册追跑_λI 0 2.1K✓·OT·oc
控w_ops_s008_v009_d0328_册追跑_λR 0 2.1K✓·OT·oc
控W=控w_ops_s008_v010_d0331_册追跑_λI 0 2.1K✓·OT·oc
推w_dp_s017_v005_d0324_初写谱净拆_λB 0 1.8K✓·OT·oc
推w_dp_s017_v005_d0324_初写谱净拆_λδ 0 1.8K✓·OT·oc
推w_dp_s017_v008_d0329_初写谱净拆_λS 0 2.0K✓·OT·oc
推w_dp_s017_v009_d0331_初写谱净拆_λI 0 2.3K✓·OT·oc
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc 0 2.6K✓·OT·oc
时P=时p_tu_s001_v004_d0321_踪稿析_λτ 0 16✓·OT
桥P=桥p_rb_s006_v003_d0317_读唤任_λΠ 0 424✓·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde 0 784✓·OT
漂P=漂p_dw_s005_v004_d0321_踪稿析_λ18 0 375✓·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde 0 531✓·OT·oc
片W=片w_sm_s026_v002_d0330_缩分话_λF 0 1.7K✓·OT·oc
环w_pc_s025_v002_d0329_读唤任_λS 0 1.9K✓·OT·oc
环w_pc_s025_v003_d0330_读唤任_λπ 0 2.0K✓·OT·oc
研w_rl_s029_v002_d0330_译改名踪_λL 0 1.3K✓·OT·oc
研w_rl_s029_v003_d0331_译改名踪_λA 0 1.9K✓·OT·oc
研W=研w_rl_s029_v005_d0401_译改名踪_λG 0 2.3K✓·OT·oc
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc 0 3.1K~·OT
编w_gc_s032_v002_d0401_读唤任_λG 0 1.9K✓·OT·oc
编W=编w_gc_s032_v003_d0401_读唤任_λG 0 1.6K✓·OT·oc
脉p_ph_s015_v004_d0403_读唤任_λP0_βoc 0 1.0K✓·OT·oc
虚F=虚f_mc_s036_v001 0 732✓·OT·oc
虚F=虚f_mc_s036_v001_llm 0 558✓·OT
虚F=虚f_mc_s036_v001_profile 0 443✓·OT
补P=补p_rwb_s022_v002_d0321_缩分话_λ18 0 460✓·OT
觉W=觉w_fc_s019_v002_d0321_缩分话_λ18 0 1.7K✓·OT·oc
警p_sa_s030_v003_d0402_缩分话_λV 0 654✓·OT
警P=警p_sa_s030_v005_d0404_缩分话_λNU 0 596✓·OT·oc
训W=训w_trwr_s028_v002_d0330_缩分话_λF 0 803✓·OT·oc
路F=路f_cxr_s027_v002_d0330_缩分话_λF 0 489✓·OT
递P=递p_sh_s023_v002_d0321_缩分话_λ18 0 654✓·OT
队P=队p_tq_s018_v002_d0317_缩分话_λQ 0 667✓·OT

  └ .operator_stats_seq008_v010_d0331__persi_artifact_detection_seq003_v001(0) .operator_stats_seq008_v010_d0331__persi_baselines_seq004_v001(0) .operator_stats_seq008_v010_d0331__persi_classify_state_seq005_v001(0) .operator_stats_seq008_v010_d0331__persi_constants_seq001_v001(0) .operator_stats_seq008_v010_d0331__persi_markdown_seq008_v001(0) .operator_stats_seq008_v010_d0331__persi_observations_seq007_v001(0) .operator_stats_seq008_v010_d0331__persi_operator_stats_seq009_v001(0) .operator_stats_seq008_v010_d0331__persi_time_utils_seq002_v001(0) .operator_stats_seq008_v010_d0331__persi_timeframes_seq006_v001(0) [2.1K]
**src/codebase_detector** (8)
层=codebase_detector_constants 1 107·OT
层=codebase_detector_profile 2 103·OT
层=codebase_detector_pigeon_state 3 553·OT
层=codebase_detector_python_state 4 141·OT
层=codebase_detector_node_state 5 146·OT
层=codebase_detector_count_modules 6 154·OT
层=codebase_detector_build_state 7 118·OT
层=codebase_detector_orchestrator 8 238·OT

**src/codebase_transmuter** (11)
控=codebase_transmuter_constants 1 427·OT
控=codebase_transmuter_telemetry_loader 2 1.0K·OT
控=codebase_transmuter_file_utils 3 213·OT
控=codebase_transmuter_numerifier_class 4 549·OT
控=codebase_transmuter_numerify 5 222·OT
控=codebase_transmuter_numerical_mirror 6 442·OT
控=codebase_transmuter_profile_extractor 7 413·OT
控=codebase_transmuter_narrator 8 1.1K·OT
控=codebase_transmuter_narrative_mirror 9 245·OT
控=codebase_transmuter_global_stats 10 913·OT
控=codebase_transmuter_orchestrator 11 126·OT

**src/cognitive** (10)
偏P=偏p_dr_s003_v002_d0315_缩分话_λν 0 815✓·OT·oc
适P=适p_ad_s001_v002_d0315_缩分话_λν 0 597✓·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν 0 734✓·OT·oc

**src/cognitive/drift** (6)
u_dbcc_s005_v001 0 228✓·OT
u_dbch_s006_v001 0 6✓·OT
u_dbs_s001_v001 0 84✓·OT
u_dcbl_s002_v001 0 187✓·OT
u_ddsd_s003_v001 0 241✓·OT
u_ddsdh_s004_v001 0 6✓·OT

**src/cognitive/drift/u_dbcc_s005_v001** (1)
u_dbcc_s005_v001_build_context 1 760·OT

  └ 偏p_dr_bcc_s004_v003_d0322_λ7(0) 偏p_dr_bs_s001_v003_d0322_λ7(0) 偏p_dr_cb_s002_v003_d0322_λ7(0) 偏p_dr_dsd_s003_v003_d0322_λ7(0) [740]
**src/cognitive/unsaid** (8)
u_uah_s007_v001 0 6✓·OT
u_ucdi_s003_v001 0 50✓·OT
u_ucp_s002_v001 0 52✓·OT
u_udd_s001_v001 0 76✓·OT
u_uep_s005_v001 0 6✓·OT
u_uet_s004_v001 0 61✓·OT
u_uo_s008_v001 0 440✓·OT
U_=u_usp_s006_v001 0 6✓·OT

**src/cognitive/unsaid/u_uo_s008_v001** (6)
u_uo_s008_v001_helpers 1 20·OT
u_uo_s008_v001_snapshots 2 21·OT
u_uo_s008_v001_deletion 3 21·OT
u_uo_s008_v001_analysis 4 21·OT
u_uo_s008_v001_summary 5 20·OT
u_uo_s008_v001_orchestrator 6 1.4K·OT

  └ 隐p_un_di_s002_v003_d0322_λ7(0) 隐p_un_he_s001_v003_d0322_λ7(0) 隐p_un_or_s003_v003_d0322_λ7(0) [731]
**src/cognitive/隐p_un_s002_v002_d0315_缩分话_λν** (7)
隐P=隐p_un_s002_v002_d0315_缩分话_λν_diff_classify 1 397·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_helpers 1 498·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_topic 2 128·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_snapshot 3 24·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_analysis 4 24·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_emotion_summary 5 26·OT
隐P=隐p_un_s002_v002_d0315_缩分话_λν_orchestrator 6 1.4K·OT

**src/context_compressor** (6)
脉=context_compressor_constants 1 77·OT
脉=context_compressor_token_utils 2 43·OT
脉=context_compressor_ast_strippers 3 252·OT
脉=context_compressor_text_cleaners 4 234·OT
脉=context_compressor_file_processor 5 193·OT
脉=context_compressor_changed_decomposed 6 502·OT

**src/engagement_hooks** (6)
写=engagement_hooks_helpers 1 206·OT
写=engagement_hooks_context 2 517·OT
写=engagement_hooks_mood 3 245·OT
写=engagement_hooks_hook_generators 5 1.7K·OT
写=engagement_hooks_hook_generators 6 1.7K·OT
写=engagement_hooks_hook_generators 7 162·OT

**src/escalation_engine** (36)
压=escalation_engine_constants 1 226·OT
压=escalation_engine_state 2 240·OT
压=escalation_engine_bug_persistence 3 191·OT
压=escalation_engine_data_loaders 3 732·OT
压=escalation_engine_data_loaders_a 3 483·OT
压=escalation_engine_dossier 4 167·OT
压=escalation_engine_entropy 5 203·OT
压=escalation_engine_registry 6 289·OT
压=escalation_engine_confidence_decomposed 7 587·OT
压=escalation_engine_fix_glob 8 138·OT
压=escalation_engine_fix_executors 9 992·OT
压=escalation_engine_fix_hardcoded 9 241·OT
压=escalation_engine_fix_dead_exports 10 387·OT
压=escalation_engine_fix_over_cap 11 371·OT
压=escalation_engine_fix_duplicate_docstring_decomposed 12 633·OT
压=escalation_engine_rollback 13 411·OT
压=escalation_engine_warnings_decomposed 14 696·OT
压=escalation_engine_logging 15 235·OT
压=escalation_engine_check_helpers 16 919·OT
压=escalation_engine_check_helpers_a 16 597·OT
压=escalation_engine_zombies 16 262·OT
压=escalation_engine_collect_modules 17 355·OT
压=escalation_engine_check_helpers_b 18 344·OT
压=escalation_engine_handle_level_decomposed 19 1.3K·OT
压=escalation_engine_orchestrator 20 609·OT
压=escalation_engine_status 21 240·OT

  压└ v001_bug_persistence(1) v001_dossier(2) v001_entropy_confidence(3) v001_registry_files(4) v001_rollback_check(5) [908]
  压└ v001_constants(1) v001_generate_warnings(2) v001_format_block(3) v001_update_file(4) v001_inject_warnings(5) [825]
**src/module_identity** (18)
MO=module_identity_constants 1 307·OT
MO=module_identity_utils 2 196·OT
MO=module_identity_alias 3 384·OT
MO=module_identity_sources 4 251·OT
MO=module_identity_lookups 5 966·OT
MO=module_identity_backstory 6 224·OT
MO=module_identity_code 7 782·OT
MO=module_identity_probes 8 1.9K·OT
MO=module_identity_coaching 9 550·OT
MO=module_identity_classify 10 403·OT
MO=module_identity_voice 11 621·OT
MO=module_identity_todo 12 459·OT
MO=module_identity_diagnose 13 370·OT
MO=module_identity_orchestrator 14 1.5K·OT

  MO└ v001_find_stale_path(1) v001_parse_ast_nodes(2) v001_extract_docstring(3) v001_wrapper(4) [868]
**src/numeric_surface** (7)
NU=numeric_surface_load 1 358·OT
NU=numeric_surface_graph 2 320·OT
NU=numeric_surface_dual 3 121·OT
NU=numeric_surface_clusters 4 315·OT
NU=numeric_surface_traversal 5 141·OT
NU=numeric_surface_build 6 20·OT
NU=numeric_surface_main 7 1.1K·OT

**src/operator_stats** (13)
u_oscl_s003_v001 0 139✓·OT
u_oscp_s004_v001 0 114✓·OT
u_oscs_s011_v001 0 120✓·OT
u_osct_s001_v001 0 30✓·OT
u_osrc_s009_v001 0 85✓·OT
u_osrd_s006_v001 0 110✓·OT
u_osrf_s010_v001 0 97✓·OT
u_osro_s008_v001 0 395✓·OT
u_osrr_s005_v001 0 110✓·OT
u_osrt_s005_v001 0 293✓·OT
u_ostd_s007_v001 0 215✓·OT
u_ostf_s007_v001 0 215✓·OT
u_ostu_s002_v001 0 51✓·OT

**src/operator_stats/u_osro_s008_v001** (4)
u_osro_s008_v001_slot_analysis 1 22·OT
u_osro_s008_v001_streak_analysis 2 23·OT
u_osro_s008_v001_time_analysis 3 22·OT
u_osro_s008_v001_render_observations 4 928·OT

**src/operator_stats/u_ostd_s007_v001** (2)
u_ostd_s007_v001_timeframe_helpers 1 23·OT
u_ostd_s007_v001_render_timeframes 2 404·OT

**src/operator_stats/u_ostf_s007_v001** (1)
u_ostf_s007_v001_render_timeframes 1 404·OT

**src/push_snapshot** (19)
PU=push_snapshot_constants 1 64·OT
PU=push_snapshot_data_loaders 2 1.4K·OT
PU=push_snapshot_registry 2 232·OT
PU=push_snapshot_self_fix 3 280·OT
PU=push_snapshot_heat_map 4 296·OT
PU=push_snapshot_deaths 5 174·OT
PU=push_snapshot_operator 6 218·OT
PU=push_snapshot_cycle_state 7 88·OT
PU=push_snapshot_probe_state 8 297·OT
PU=push_snapshot_compute_stats 9 487·OT
PU=push_snapshot_file_stats 9 310·OT
PU=push_snapshot_coupling 10 196·OT
PU=push_snapshot_persistence 11 355·OT
PU=push_snapshot_health_score_decomposed 12 489·OT
PU=push_snapshot_biggest_moves 13 323·OT
PU=push_snapshot_history 14 160·OT
PU=push_snapshot_compute_drift_decomposed 15 1.0K·OT
PU=push_snapshot_inject_drift_decomposed 16 732·OT
PU=push_snapshot_capture_decomposed 17 1.0K·OT

**src/scale_inference** (4)
SC=scale_inference_constants 1 260·OT
SC=scale_inference_scale_to 2 308·OT
SC=scale_inference_helpers 3 21·OT
SC=scale_inference_main 4 728·OT

**src/tc_context** (15)
tc_context_cache 1 58·OT
tc_context_telemetry 2 190·OT
tc_context_unsaid 3 162·OT
tc_context_entropy 4 177·OT
tc_context_heatmap 5 212·OT
tc_context_topology 6 166·OT
tc_context_bugs 7 148·OT
tc_context_self_fix 8 129·OT
tc_context_session_info 9 181·OT
tc_context_interrogation 10 178·OT
tc_context_organism 11 172·OT
tc_context_prompts 12 171·OT
tc_context_session_chat 13 295·OT
tc_context_profiles 14 241·OT
tc_context_orchestrator 15 256·OT

**src/tc_profile** (44)
tc_profile_constants 1 742·OT
tc_profile_state 2 19·OT
tc_profile_empty_structs 3 2.6K·OT
tc_profile_empty_profile_decomposed 4 1.4K·OT
tc_profile_empty_section_decomposed 5 1.2K·OT
tc_profile_section_classify 6 291·OT
tc_profile_update_section_decomposed 7 1.4K·OT
tc_profile_intelligence_deductions 9 2.7K·OT
tc_profile_intelligence_deductions_a 9 1.4K·OT
tc_profile_intelligence_comfort 10 384·OT
tc_profile_intelligence_deductions 10 317·OT
tc_profile_intelligence_deletion_time 11 1.1K·OT
tc_profile_intelligence_deletion 12 593·OT
tc_profile_intelligence_time 13 497·OT
tc_profile_intelligence_deductions_b 14 1.6K·OT
tc_profile_intelligence_frustration_suppression 15 850·OT
tc_profile_intelligence_frustration 16 553·OT
tc_profile_intelligence_suppression 17 319·OT
tc_profile_intelligence_decision_work 18 732·OT
tc_profile_intelligence_decision 19 401·OT
tc_profile_intelligence_work 20 353·OT
tc_profile_intelligence_contradiction 21 500·OT
tc_profile_intelligence_behavioral_laws 22 241·OT
tc_profile_intelligence_persist 23 149·OT
tc_profile_intelligence_orchestrator 24 482·OT
tc_profile_format_intelligence_decomposed 25 742·OT
tc_profile_mine_code_style_decomposed 26 1.6K·OT
tc_profile_mine_code_style_scanner 27 23·OT
tc_profile_mine_code_style_analyzer 28 24·OT
tc_profile_mine_code_style_compiler 29 1.6K·OT
tc_profile_load_save 30 256·OT
tc_profile_update_completion_decomposed 31 1.5K·OT
tc_profile_update_composition_decomposed 32 875·OT
tc_profile_bootstrap_decomposed 33 2.1K·OT
tc_profile_bootstrap_compositions 34 23·OT
tc_profile_bootstrap_completions 35 23·OT
tc_profile_bootstrap_finalize 36 2.1K·OT
tc_profile_format_profile_decomposed 37 1.3K·OT
tc_profile_intent_generation 38 679·OT
tc_profile_intent_extractors 39 459·OT
tc_profile_intent_template 40 243·OT
tc_profile_generate_session 41 471·OT
tc_profile_generate_session_decomposed 42 474·OT
tc_profile_generate_journal 43 197·OT

**src/tc_sim** (30)
tc_sim_constants 1 147·OT
tc_sim_helpers 2 293·OT
tc_sim_classes 3 372·OT
tc_sim_extract 4 482·OT
tc_sim_pause 5 569·OT
tc_sim_score 6 381·OT
tc_sim_historical 7 1.1K·OT
tc_sim_replay 8 847·OT
tc_sim_report 9 713·OT
tc_sim_report_basic 10 368·OT
tc_sim_report_summary 11 369·OT
tc_sim_export 12 263·OT
tc_sim_memory 13 654·OT
tc_sim_memory_core 14 389·OT
tc_sim_memory_update 15 291·OT
tc_sim_narrate_helpers 16 192·OT
tc_sim_narrate_chapters 17 659·OT
tc_sim_narrate_small 18 263·OT
tc_sim_narrate_chapter5 19 418·OT
tc_sim_narrate_chapter2 20 656·OT
tc_sim_narrate_chapter3 21 656·OT
tc_sim_narrate_chapter4 22 1.1K·OT
tc_sim_narrate_main 23 157·OT
tc_sim_transcript 24 1.6K·OT
tc_sim_diagnose 25 501·OT
tc_sim_fix 26 1.0K·OT
tc_sim_main 27 1.7K·OT

  └ v001_print_session(1) v001_print_result(2) v001_print_summary(3) [775]
**src/tc_web** (5)
TC=tc_web_html 1 742·OT
TC=tc_web_handler 2 18·OT
TC=tc_web_server 3 614·OT

  TC└ v001_html_const(1) v001_orchestrator(2) [772]
**src/thought_completer** (1)
TH=thought_completer_main 1 309·OT

**src/u_pd_s024_v001** (7)
u_pd_s024_v001_constants 1 58·OT
u_pd_s024_v001_colorize 2 113·OT
u_pd_s024_v001_section_text 3 228·OT
u_pd_s024_v001_load_snapshots 4 95·OT
u_pd_s024_v001_list_sections 5 146·OT
u_pd_s024_v001_diff_block 6 259·OT
u_pd_s024_v001_main 7 161·OT

**src/u_pe_s024_v002_d0402_λC** (13)
u_pe_s024_v002_d0402_λC_block_builder_seq013_v001 0 6✓·OT
u_pe_s024_v002_d0402_λC_block_utils2_seq010_v001 0 63✓·OT
u_pe_s024_v002_d0402_λC_block_utils_seq009_v001 0 157✓·OT
u_pe_s024_v002_d0402_λC_constants_seq001_v001 0 49✓·OT
u_pe_s024_v002_d0402_λC_context_gatherers2_seq004_v001 0 345✓·OT
u_pe_s024_v002_d0402_λC_context_gatherers3_seq005_v001 0 227✓·OT
u_pe_s024_v002_d0402_λC_context_gatherers4_seq006_v001 0 105✓·OT
u_pe_s024_v002_d0402_λC_context_gatherers_seq003_v001 0 498✓·OT
u_pe_s024_v002_d0402_λC_enricher_core_seq008_v001 0 218✓·OT
u_pe_s024_v002_d0402_λC_injector_seq011_v001 0 266✓·OT
u_pe_s024_v002_d0402_λC_injector_wrapper_seq012_v001 0 266✓·OT
u_pe_s024_v002_d0402_λC_prompt_builder_seq007_v001 0 443✓·OT
u_pe_s024_v002_d0402_λC_utils_seq002_v001 0 67✓·OT

**src/u_pe_s024_v004_d0403_λP0_βoc** (10)
u_pe_s024_v004_d0403_λP0_βoc_block_utils_seq008_v001 0 157✓·OT
u_pe_s024_v004_d0403_λP0_βoc_bug_routing_seq005_v001 0 167✓·OT
u_pe_s024_v004_d0403_λP0_βoc_bug_scoring_seq004_v001 0 306✓·OT
u_pe_s024_v004_d0403_λP0_βoc_constants_seq001_v001 0 49✓·OT
u_pe_s024_v004_d0403_λP0_βoc_data_loaders_seq003_v001 0 498✓·OT
u_pe_s024_v004_d0403_λP0_βoc_enricher_seq007_v001 0 228✓·OT
u_pe_s024_v004_d0403_λP0_βoc_injector_seq009_v001 0 225✓·OT
u_pe_s024_v004_d0403_λP0_βoc_main_seq010_v001 0 6✓·OT
u_pe_s024_v004_d0403_λP0_βoc_prompt_builder_seq006_v001 0 448✓·OT
u_pe_s024_v004_d0403_λP0_βoc_utils_seq002_v001 0 67✓·OT

**src/u_pj_s019_v002_d0402_λC** (17)
u_pj_s019_v002_d0402_λC_build_snapshot_decomposed_seq012_v001 0 162✓·OT
u_pj_s019_v002_d0402_λC_candidate_compositions_seq005_v001 0 97✓·OT
u_pj_s019_v002_d0402_λC_coaching_utils_seq009_v001 0 92✓·OT
u_pj_s019_v002_d0402_λC_composition_utils_seq004_v001 0 113✓·OT
u_pj_s019_v002_d0402_λC_constants_seq001_v001 0 151✓·OT
u_pj_s019_v002_d0402_λC_intent_classification_seq007_v001 0 88✓·OT
u_pj_s019_v002_d0402_λC_log_enriched_entry_decomposed_seq016_v001 0 650✓·OT
u_pj_s019_v002_d0402_λC_predict_next_issues_decomposed_seq011_v001 0 330✓·OT
u_pj_s019_v002_d0402_λC_refresh_copilot_seq014_v001 0 162✓·OT
u_pj_s019_v002_d0402_λC_refresh_utils_seq015_v001 0 137✓·OT
u_pj_s019_v002_d0402_λC_running_stats_decomposed_seq010_v001 0 229✓·OT
u_pj_s019_v002_d0402_λC_select_composition_seq006_v001 0 214✓·OT
u_pj_s019_v002_d0402_λC_snapshot_io_seq013_v001 0 182✓·OT
u_pj_s019_v002_d0402_λC_system_state_seq008_v001 0 211✓·OT
u_pj_s019_v002_d0402_λC_text_processing_seq003_v001 0 124✓·OT
u_pj_s019_v002_d0402_λC_utils_seq002_v001 0 141✓·OT
u_pj_s019_v002_d0402_λC_write_snapshot_seq013_v001 0 34✓·OT

**src/u_pj_s019_v003_d0404_λNU_βoc** (30)
u_pj_s019_v003_d0404_λNU_βoc_constants 1 513·OT
u_pj_s019_v003_d0404_λNU_βoc_utils 2 344·OT
u_pj_s019_v003_d0404_λNU_βoc_text_matching 3 286·OT
u_pj_s019_v003_d0404_λNU_βoc_composition_key 4 124·OT
u_pj_s019_v003_d0404_λNU_βoc_meta_hook 5 106·OT
u_pj_s019_v003_d0404_λNU_βoc_intent 6 83·OT
u_pj_s019_v003_d0404_λNU_βoc_module_refs 7 210·OT
u_pj_s019_v003_d0404_λNU_βoc_recent_bindings 8 205·OT
u_pj_s019_v003_d0404_λNU_βoc_candidate_comps 9 304·OT
u_pj_s019_v003_d0404_λNU_βoc_select_composition 10 460·OT
u_pj_s019_v003_d0404_λNU_βoc_skip_duplicate 11 149·OT
u_pj_s019_v003_d0404_λNU_βoc_telemetry_loaders 12 427·OT
u_pj_s019_v003_d0404_λNU_βoc_running_stats_decomposed 13 701·OT
u_pj_s019_v003_d0404_λNU_βoc_predict_issues_decomposed 14 805·OT
u_pj_s019_v003_d0404_λNU_βoc_build_snapshot_decomposed 15 598·OT
u_pj_s019_v003_d0404_λNU_βoc_coaching 16 232·OT
u_pj_s019_v003_d0404_λNU_βoc_meta_hook_builder 17 388·OT
u_pj_s019_v003_d0404_λNU_βoc_refresh_utils 18 409·OT
u_pj_s019_v003_d0404_λNU_βoc_force_fresh 19 241·OT
u_pj_s019_v003_d0404_λNU_βoc_write_snapshot 20 105·OT
u_pj_s019_v003_d0404_λNU_βoc_refresh_copilot 21 499·OT
u_pj_s019_v003_d0404_λNU_βoc_entry_builders 22 494·OT
u_pj_s019_v003_d0404_λNU_βoc_extract_composition 23 511·OT
u_pj_s019_v003_d0404_λNU_βoc_write_raw 24 260·OT
u_pj_s019_v003_d0404_λNU_βoc_append_journal 25 110·OT
u_pj_s019_v003_d0404_λNU_βoc_post_append 26 163·OT
u_pj_s019_v003_d0404_λNU_βoc_gemini_enricher 27 575·OT
u_pj_s019_v003_d0404_λNU_βoc_training_pair 28 220·OT
u_pj_s019_v003_d0404_λNU_βoc_staleness_alert 29 171·OT
u_pj_s019_v003_d0404_λNU_βoc_orchestrator 30 491·OT

**src/u_psg_s026_v001** (3)
u_psg_s026_v001_constants 1 36·OT
u_psg_s026_v001_loaders 2 286·OT
u_psg_s026_v001_logger 3 498·OT

**src/unsaid_accumulator** (5)
UN=unsaid_accumulator_constants 1 56·OT
UN=unsaid_accumulator_record 2 222·OT
UN=unsaid_accumulator_query 3 226·OT
UN=unsaid_accumulator_get_recent 4 105·OT
UN=unsaid_accumulator_get_summary 5 168·OT

**src/修_sf_s013** (11)
修f_sf_aaif_s011_v002_d0329_λH 0 393✓·OT
修f_sf_aco_s009_v003_d0402_λVR 0 330✓·OT
修f_sf_rsf_s008_v002_d0329_λH 0 209✓·OT
修f_sf_sb_s010_v002_d0329_λH 0 80✓·OT
修f_sf_scfc_s004_v002_d0329_λH 0 213✓·OT
修f_sf_sdd_s003_v002_d0329_λH 0 113✓·OT
修f_sf_sde_s006_v002_d0329_λH 0 231✓·OT
修f_sf_sh_s001_v002_d0329_λH 0 160✓·OT
修f_sf_sohc_s005_v002_d0329_λH 0 194✓·OT
修f_sf_sqn_s002_v002_d0329_λH 0 88✓·OT
修F=修f_sf_wr_s007_v002_d0329_λH 0 194✓·OT

**src/修f_sf_s013_v012_d0402_初写谱净拆_λVR** (16)
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_apply_import_fixes_seq012_v001 0 379✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_compile_helpers_seq010_v001 0 6✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_compile_oversized_seq009_v001 0 330✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_constants_seq001_v001 0 22✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_import_injector_seq014_v001 0 6✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_import_processor_seq013_v001 0 6✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_problem_collector_seq016_v001 0 6✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_run_self_fix_seq015_v001 0 209✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_cross_file_coupling_seq006_v001 0 213✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_dead_exports_seq004_v001 0 231✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_duplicate_docstrings_seq005_v001 0 113✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_hardcoded_seq003_v001 0 176✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_over_hard_cap_seq007_v001 0 194✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_query_noise_seq008_v001 0 88✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_seq_base_seq002_v001 0 80✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_write_self_fix_report_seq011_v001 0 194✓·OT

**src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc** (12)
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_auto_apply_import_fixes_seq011_v001 0 379✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_auto_compile_oversized_seq009_v001 0 330✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_constants_seq001_v001 0 22✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_run_self_fix_seq012_v001 0 209✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_cross_file_coupling_seq007_v001 0 213✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_dead_exports_seq005_v001 0 231✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_duplicate_docstrings_seq006_v001 0 113✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_hardcoded_seq003_v001 0 176✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_over_hard_cap_seq008_v001 0 194✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_query_noise_seq004_v001 0 88✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_seq_base_seq002_v001 0 80✓·OT
修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_write_self_fix_report_seq010_v001 0 194✓·OT

**src/叙p_pn_s012_v006_d0328_初写谱净拆_λR** (6)
叙p_pn_s012_v006_d0328_初写谱净拆_λR_build_briefs 1 285·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR_load_snapshot 2 117·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR_deepseek_call 3 246·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR_narrative_helpers 4 27·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR_narrative_prompt 5 1.0K·OT
叙p_pn_s012_v006_d0328_初写谱净拆_λR_orchestrator 6 469·OT

**src/叙p_pn_s012_v007_d0403_初写谱净拆_λP0** (6)
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_narrative_prompt_helpers 1 29·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_narrative_prompt_wrapper 2 1.0K·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_file_briefs 3 285·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_deepseek_call 4 246·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_load_snapshot 5 117·OT
叙p_pn_s012_v007_d0403_初写谱净拆_λP0_orchestrator 6 469·OT

**src/叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc** (7)
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_file_briefs_seq003_v001 0 99✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_narrative_subhelpers_seq005_v001 0 6✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_narrative_wrapper_seq006_v001 0 489✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_call_deepseek_seq004_v001 0 72✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_generate_narrative_seq007_v001 0 199✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_load_composition_seq002_v001 0 47✓·OT
叙P=叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_prompt_templates_seq001_v001 0 6✓·OT

**src/合p_us_s026_v002_d0330_缩分话_λF** (6)
合P=合p_us_s026_v002_d0330_缩分话_λF_utils 1 309·OT
合P=合p_us_s026_v002_d0330_缩分话_λF_nearest 2 172·OT
合p_us_us_s026_v002_d0330_缩分话_λF_merge_core 3 25·OT
合P=合p_us_s026_v002_d0330_缩分话_λF_merge_signals 4 895·OT
合P=合p_us_s026_v002_d0330_缩分话_λF_write_log 5 395·OT
合P=合p_us_s026_v002_d0330_缩分话_λF_main 6 23·OT

**src/对p_tp_s027_v003_d0402_缩分话_λVR_βoc** (6)
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_capture_decomposed_seq005_v001 0 312✓·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_intent_classifiers_seq002_v001 0 168✓·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_matching_seq003_v001 0 116✓·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_note_builders_seq004_v001 0 86✓·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_summary_decomposed_seq006_v001 0 445✓·OT
对P=对p_tp_s027_v003_d0402_缩分话_λVR_βoc_utils_seq001_v001 0 185✓·OT

**src/层w_sl_s007_v003_d0317_读唤任_λΠ** (15)
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_constants 1 202·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_stream_client 2 191·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_alert 3 96·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_aggregation_bucket 4 662·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_stream_formatter 5 488·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_connection_pool 6 810·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_event_aggregator 7 768·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_metrics_collector 8 729·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_alert_engine 9 1.3K·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_session_replay 10 875·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_live_dashboard 11 787·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_telemetry_http_handler 12 1.1K·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_streaming_telemetry_server 13 1.2K·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_simulation_helpers 14 145·OT
层W=层w_sl_s007_v003_d0317_读唤任_λΠ_demo_orchestrator 15 562·OT

**src/录p_lo_s003_v005_d0322_译改名踪_λω** (2)
录P=录p_lo_s003_v005_d0322_译改名踪_λω_load_src 1 158·OT
录P=录p_lo_s003_v005_d0322_译改名踪_λω_telemetry_class 2 1.3K·OT

**src/忆_qm_s010** (6)
忆p_qm_cl_s004_v002_d0329_λH 0 112✓·OT
忆p_qm_co_s001_v002_d0329_λH 0 25✓·OT
忆p_qm_fi_s002_v002_d0329_λH 0 52✓·OT
忆p_qm_lm_s006_v002_d0329_λH 0 158✓·OT
忆p_qm_rq_s005_v002_d0329_λH 0 134✓·OT
忆P=忆p_qm_tu_s003_v002_d0329_λH 0 71✓·OT

**src/思_cr_s014** (14)
思f_cr_ac_s007_v002_d0322_λ7 0 6✓·OT
思f_cr_ch_s004_v002_d0322_λ7 0 99✓·OT
思f_cr_co_s001_v002_d0322_λ7 0 43✓·OT
思f_cr_dm_s012_v002_d0322_λ7 0 326✓·OT
思f_cr_dm_s012_v003_d0331_λM 0 326✓·OT
思f_cr_dp_s003_v002_d0322_λ7 0 273✓·OT
思f_cr_pb_s006_v002_d0322_λ7 0 6✓·OT
思f_cr_pg_s005_v002_d0322_λ7 0 327✓·OT
思f_cr_pw_s011_v002_d0322_λ7 0 394✓·OT
思f_cr_pw_s011_v003_d0331_λM 0 394✓·OT
思f_cr_rc_s008_v002_d0322_λ7 0 384✓·OT
思f_cr_rl_s009_v002_d0322_λ7 0 6✓·OT
思f_cr_sfr_s010_v002_d0322_λ7 0 6✓·OT
思F=思f_cr_so_s002_v002_d0322_λ7 0 54✓·OT

**src/探p_ur_s024_v002_d0329_读唤任_λS** (5)
探p_ur_s024_v002_d0329_读唤任_λS_constants 1 274·OT
探p_ur_s024_v002_d0329_读唤任_λS_load_api_key 2 101·OT
探p_ur_s024_v002_d0329_读唤任_λS_call_gemini 3 365·OT
探p_ur_s024_v002_d0329_读唤任_λS_reconstruct_helpers 4 27·OT
探p_ur_s024_v002_d0329_读唤任_λS_reconstruct_orchestrator 5 584·OT

**src/探p_ur_s024_v003_d0331_读唤任_λI** (5)
探P=探p_ur_s024_v003_d0331_读唤任_λI_constants 1 486·OT
探P=探p_ur_s024_v003_d0331_读唤任_λI_load_api_key 2 101·OT
探P=探p_ur_s024_v003_d0331_读唤任_λI_call_gemini 3 391·OT
探P=探p_ur_s024_v003_d0331_读唤任_λI_reconstruct_helpers 4 27·OT
探P=探p_ur_s024_v003_d0331_读唤任_λI_reconstruct_wrapper 5 723·OT

**src/控_ost_s008** (9)
控f_ost_ad_s003_v001 0 87✓·OT
控f_ost_ba_s004_v001 0 216✓·OT
控f_ost_cl_s009_v001 0 258✓·OT
控f_ost_co_s001_v001 0 33✓·OT
控f_ost_cs_s005_v001 0 336✓·OT
控f_ost_ma_s008_v001 0 441✓·OT
控f_ost_ob_s007_v001 0 406✓·OT
控f_ost_ti_s006_v001 0 235✓·OT
控F=控f_ost_tu_s002_v001 0 48✓·OT

**src/推_dp_s017** (15)
推w_dp_bch_s010_v001 0 6✓·OT
推w_dp_bcm_s011_v001 0 549✓·OT
推w_dp_cc_s009_v001 0 118✓·OT
推w_dp_da_s006_v001 0 228✓·OT
推w_dp_daa_s006_v001 0 196✓·OT
推w_dp_dab_s007_v001 0 42✓·OT
推w_dp_fc_s008_v001 0 183✓·OT
推w_dp_gh_s002_v001 0 118✓·OT
推w_dp_ic_s012_v001 0 85✓·OT
推w_dp_ju_s001_v001 0 56✓·OT
推w_dp_ma_s004_v001 0 290✓·OT
推w_dp_ma_s013_v001 0 6✓·OT
推w_dp_maa_s004_v001 0 177✓·OT
推w_dp_mab_s005_v001 0 123✓·OT
推w_dp_pa_s003_v001 0 157✓·OT

**src/推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc** (33)
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_constants 1 367·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_utils 2 444·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_utils_a 2 361·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_utils_b 3 115·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_prompt_basic 4 273·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_prompt_data 4 617·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_unsaid_reconstructions 5 380·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_git_history 6 374·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_hot_modules 7 236·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_metrics 7 598·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_other_metrics 8 397·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_narrative 9 541·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_narrative_risks 9 261·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_fixes_coaching 10 315·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_consciousness 11 893·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_file_consciousness 11 509·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_codebase_health 12 418·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation 13 576·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_decomposed 13 579·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_wrapper 13 578·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_analysis 14 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_helpers 14 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_patch 15 27·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_dossier 16 223·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_injection_utils 17 172·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_build_context_decomposed 18 1.5K·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_build_wrapper 18 1.5K·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_context_collect 19 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_context_helpers_a 19 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_context_header_unsaid 20 29·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_context_helpers_b 21 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_context_helpers_c 22 28·OT
推W=推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_inject 23 238·OT

**src/桥p_rb_s006_v003_d0317_读唤任_λΠ** (4)
桥P=桥p_rb_s006_v003_d0317_读唤任_λΠ_analyzer 1 1.1K·OT
桥P=桥p_rb_s006_v003_d0317_读唤任_λΠ_session_loader 2 26·OT
桥P=桥p_rb_s006_v003_d0317_读唤任_λΠ_profile_computer 3 26·OT
桥P=桥p_rb_s006_v003_d0317_读唤任_λΠ_resistance_signal 4 26·OT

**src/测p_rwd_s009_v006_d0403_译改名踪_λP0_βde** (6)
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_score_rework 1 410·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_score_composition 2 370·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_load_stats 3 303·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_record_update 4 624·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_update_dossier 4 346·OT
测P=测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_record_rework 5 314·OT

**src/漂p_dw_s005_v004_d0321_踪稿析_λ18** (4)
漂P=漂p_dw_s005_v004_d0321_踪稿析_λ18_line_count 1 55·OT
漂P=漂p_dw_s005_v004_d0321_踪稿析_λ18_preamble_parser 2 191·OT
漂P=漂p_dw_s005_v004_d0321_踪稿析_λ18_context_budget_loader 3 133·OT
漂P=漂p_dw_s005_v004_d0321_踪稿析_λ18_drift_watcher 4 604·OT

**src/热p_fhm_s011_v005_d0403_踪稿析_λP0_βde** (12)
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_constants 1 143·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_utils 2 301·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_edit_events 3 321·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_loaders 3 794·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_entropy 4 170·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_heat_map 5 191·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_registry 6 227·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_count_touches 7 272·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_brain_helpers 8 27·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_brain_map 9 1.2K·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_update_helpers 10 27·OT
热P=热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_update_heat 11 580·OT

**src/环_pc_s025** (9)
环w_pc_co_s001_v002_d0329_λH 0 20✓·OT
环w_pc_co_s005_v002_d0329_λH 0 242✓·OT
环w_pc_lo_s002_v002_d0329_λH 0 157✓·OT
环w_pc_mc_s006_v002_d0329_λH 0 308✓·OT
环w_pc_or_s008_v002_d0329_λH 0 274✓·OT
环w_pc_or_s008_v003_d0330_λL 0 274✓·OT
环w_pc_pi_s007_v002_d0329_λH 0 241✓·OT
环w_pc_se_s003_v002_d0329_λH 0 247✓·OT
环W=环w_pc_sy_s004_v002_d0329_λH 0 287✓·OT

**src/管_cpm_s020** (15)
管w_cpm_ai_s005_v002_d0322_λ7 0 233✓·OT
管w_cpm_au_s008_v002_d0322_λ7 0 219✓·OT
管w_cpm_bu_s002_v002_d0322_λ7 0 121✓·OT
管w_cpm_co_s001_v002_d0322_λ7 0 62✓·OT
管w_cpm_in_s009_v002_d0322_λ7 0 177✓·OT
管w_cpm_ju_s003_v002_d0322_λ7 0 85✓·OT
管w_cpm_op_s004_v002_d0322_λ7 0 170✓·OT
管w_cpm_or_s010_v003_d0401_λG 0 147✓·OT
管w_cpm_os_s006_v002_d0322_λ7 0 230✓·OT
管W=管w_cpm_tu_s007_v002_d0322_λ7 0 114✓·OT

  └ auto_index_builder_seq005b_v001(0) auto_index_helpers_seq005a_v001(0) index_injector_seq009b_v001(0) state_injector_seq009c_v001(0) telemetry_injector_seq009a_v001(0) [769]
**src/管w_cpm_s020_v003_d0402_缩分话_λVR_βoc** (15)
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_audit_decomposed_seq009_v001 0 236✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_auto_index_decomposed_seq005_v001 0 399✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_block_utils_seq002_v001 0 133✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_bug_voices_seq006_v001 0 178✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_constants_seq001_v001 0 217✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_file_utils_seq003_v001 0 122✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_seq011_v001 0 228✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_telemetry_seq012_v001 0 128✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_voices_state_seq013_v001 0 112✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_main_seq015_v001 0 6✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_operator_state_decomposed_seq007_v001 0 388✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_operator_state_helpers_seq008_v001 0 6✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_refresh_decomposed_seq010_v002_d0403__auto_extracted_by_pigeon_compiler_lc_p0_p3_attribution 0 323✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_registry_utils_seq004_v001 0 454✓·OT
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_render_seq014_v001 0 128✓·OT

**src/管w_cpm_s020_v005_d0404_缩分话_λNU_βoc** (10)
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_constants 1 319·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_block_utils 2 225·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_json_utils 3 84·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_render_utils 4 157·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_upsert 5 117·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_audit_helpers 6 27·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_audit_main 7 780·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_inject_telemetry 8 192·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_inject_index 9 180·OT
管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_main 10 25·OT

**src/脉_ph_s015** (7)
脉p_ph_co_s001_v001 0 53✓·OT
脉p_ph_in_s003_v001 0 160✓·OT
脉p_ph_jo_s006_v001 0 56✓·OT
脉p_ph_or_s007_v001 0 233✓·OT
脉p_ph_rc_s004_v001 0 195✓·OT
脉p_ph_st_s005_v001 0 70✓·OT
脉P=脉p_ph_ut_s002_v001 0 59✓·OT

**src/虚f_mc_s036_v001** (4)
虚F=虚f_mc_s036_v001_constants 1 65·OT
虚F=虚f_mc_s036_v001_detect_voids 2 334·OT
虚F=虚f_mc_s036_v001_generate_tasks 3 650·OT
虚F=虚f_mc_s036_v001_scan_missing_context 4 587·OT

**src/虚f_mc_s036_v001_profile** (6)
虚F=虚f_mc_s036_v001_profile_is_real_module_name 1 54·OT
虚F=虚f_mc_s036_v001_profile_jload 2 78·OT
虚F=虚f_mc_s036_v001_profile_read_source 3 135·OT
虚F=虚f_mc_s036_v001_profile_top_hesitation_files 4 204·OT
虚F=虚f_mc_s036_v001_profile_find_module_path 5 271·OT
虚F=虚f_mc_s036_v001_profile_build_file_profile 6 530·OT

**src/补p_rwb_s022_v002_d0321_缩分话_λ18** (5)
补P=补p_rwb_s022_v002_d0321_缩分话_λ18_utils 1 182·OT
补P=补p_rwb_s022_v002_d0321_缩分话_λ18_loaders 2 403·OT
补P=补p_rwb_s022_v002_d0321_缩分话_λ18_backfill 3 470·OT
补P=补p_rwb_s022_v002_d0321_缩分话_λ18_backfill_core 4 26·OT
补P=补p_rwb_s022_v002_d0321_缩分话_λ18_backfill_orchestrator 5 474·OT

**src/觉_fc_s019** (12)
觉w_fc_au_s004_v002_d0329_λH 0 122✓·OT
觉w_fc_cl_s007_v002_d0329_λH 0 88✓·OT
觉w_fc_da_s010_v002_d0329_λH 0 325✓·OT
觉w_fc_de_s005_v002_d0329_λH 0 269✓·OT
觉w_fc_de_s006_v002_d0329_λH 0 175✓·OT
觉w_fc_dh_s011_v002_d0329_λH 0 6✓·OT
觉w_fc_dw_s012_v002_d0329_λH 0 325✓·OT
觉w_fc_he_s001_v002_d0329_λH 0 214✓·OT
觉w_fc_mo_s009_v002_d0329_λH 0 101✓·OT
觉w_fc_pb_s008_v002_d0329_λH 0 63✓·OT
觉w_fc_pe_s002_v002_d0329_λH 0 58✓·OT
觉w_fc_re_s003_v002_d0329_λH 0 202✓·OT

**src/警p_sa_s030_v003_d0402_缩分话_λV** (8)
警p_sa_s030_v003_d0402_缩分话_λV_check_staleness_helpers_seq005_v001 0 6✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_check_staleness_seq006_v001 0 167✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_constants_seq001_v001 0 100✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_extract_block_seq004_v001 0 44✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_inject_alert_seq008_v001 0 237✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_inject_helpers_seq007_v001 0 6✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_parse_ts_seq002_v001 0 31✓·OT
警p_sa_s030_v003_d0402_缩分话_λV_strip_alert_seq003_v001 0 24✓·OT

**src/路f_cxr_s027_v002_d0330_缩分话_λF** (5)
路F=路f_cxr_s027_v002_d0330_缩分话_λF_trigrams 1 71·OT
路F=路f_cxr_s027_v002_d0330_缩分话_λF_tokenize 2 50·OT
路F=路f_cxr_s027_v002_d0330_缩分话_λF_format 3 321·OT
路F=路f_cxr_s027_v002_d0330_缩分话_λF_score 4 414·OT
路F=路f_cxr_s027_v002_d0330_缩分话_λF_route 5 244·OT

**streaming_layer** (19)
踪=f_sla_s006_v003_d0328_意_λR 0 308✓·OT
f_slal_s008_v003_d0328_读_λR 0 399✓·OT
f_slcp_s005_v003_d0328_读_λR 0 254✓·OT
f_slo_s016_v003_d0328_缩分话_λR 0 370✓·OT
F_=f_slo_s017_v002_d0315_缩分话_λν 0 22✓·OT
p_slc_s001_v002_d0315_缩话描_λν 0 85✓·OT
p_sld_s010_v003_d0328_唤任脉运_λR 0 205✓·OT
p_sldc_s004_v002_d0315_读_λν 0 243✓·OT
p_sldc_s005_v002_d0315_读_λν 0 77✓·OT
p_sldc_s006_v002_d0315_读_λν 0 38✓·OT
p_sldf_s013_v002_d0315_λν 0 107✓·OT
p_sldf_s014_v002_d0315_λν 0 83✓·OT
p_slds_s014_v002_d0315_λν 0 70✓·OT
p_sldy_s013_v002_d0315_缩话描_λν 0 77✓·OT
p_slf_s004_v002_d0315_读谱_λν 0 159✓·OT
p_slr_s009_v002_d0315_话读_λν 0 328✓·OT
P_=p_slsh_s002_v002_d0315_λν 0 57✓·OT
w_slhh_s011_v003_d0328_读观_λR 0 271✓·OT
W_=w_slm_s007_v003_d0328_意描_λR 0 236✓·OT

**tests/interlink** (5)
test_prompt_recon 16 621·OT
test_prompt_journal 19 397·OT
test_copilot_prompt_manager 20 403·FX
test_prompt_enricher 24 512·OT
test_prompt_signal 26 611·OT

**vscode-extension** (2)
测=classify_bridge 0 3.1K~·OT
pulse_watcher 0 175✓·OT

**Infra**
(root): _audit_compliance, _build_organism_health, _export_dev_story, _fix_broken_inits, _fix_literal_newlines, _fix_stale_globs, _run_abbrev_rename, _run_glyph_rename, _run_post_cycle, _run_smart_rename, _seed_historical_vitals, _seed_intent_numeric, _seed_pigeon_names, _tmp_clots_audit, _tmp_oc_check, _tmp_orphan_paths, _tmp_profile_dump, autonomous_dev_stress_test, deep_stress_test, deep_test, final_verify, regen_health, regen_snapshot, stress_test, stress_test_compression, stress_test_tc, test_all, test_public_release, test_tc_intent, test_training_pairs, verify_health, verify_snapshot, watchdog
client: .chat_composition_analyzer_decomposed, chat_composition_analyzer, chat_composition_analyzer_seq001_v001, chat_response_reader_seq001_v001, composition_recon_seq001_v001, os_hook, prompt_telemetry_daemon, pulse_harvest_daemon, telemetry_cleanup_seq001_v001, uia_reader_seq001_v001, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
<!-- pigeon:bug-voices -->
## Bug Voices

*Persistent bug demons minted from registry scars - active filename bugs first.*

- `u_cs_s033_v001` d0418v000 · oc `Split Fiend of ucss033v` x2 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `典w_sd_s031_v002_d0401_缩分话_λG` d0418v000 · oc `Split Fiend of wsds031v` x2 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `净拆f_rcs_s010_v006_d0322_译测编深划_λW` d0418v000 · oc `Shard Hunger of frcss010` x2 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `引w_ir_s003_v005_d0403_踪稿析_λFX` d0418v000 · oc `Overcap Maw of wirs003v` x2 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `正f_cmp_s008_v004_d0315_踪稿析_λν` d0418v000 · oc `Shard Hunger of fcmps008` x2 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
<!-- /pigeon:bug-voices -->
<!-- pigeon:operator-probes -->
## Operator Probes

*Auto-generated 2026-04-18 00:19 UTC Â· 3 probe(s) from live signals*

**ASK these questions naturally in your next response (pick 1-2, weave into context):**

1. Your deleted words predict these themes in 3 months: "use", "rephraser", "can we find a way to s". Are any of these actually where you're headed â€” or has your thinking shifted?
2. `self_heal` is trending toward abandonment. Intentional deprioritization or just hasn't come up yet?
3. You haven't named a specific module recently. What are you actually trying to build or fix right now?

*Probes are generated from: intent predictions (1wk/1mo/3mo), unsaid threads, escalation state, cognitive heat, persona memory, and operator state.*
<!-- /pigeon:operator-probes -->
<!-- pigeon:hooks -->
## Engagement Hooks

*Auto-generated 2026-04-18 00:19 UTC -- every number is measured, every dare is real.*

- You were also gonna say: "the drift watcher should track module renames after pigeon splits". That thought didn't delete. It filed itself. Name it or I will.
- Rework rate: 0%. Model is tracking your intent accurately. This is the window to push harder, not safer.
- `_build_organism_health` -- 417 days. Last generation's code. Either works perfectly or nobody knows it's broken.
- `ç®—f_ps` and `æµ‹p_rwd` (coupling=0.8). Can't be edited independently. Share imports, fears, churn cycles. Merge them or cut the dependency. The coupling is a wound.
- Gemini API key is dead (403 Forbidden). Enricher has been writing empty blocks for 4h. Every prompt since then flew blind â€” no enriched intent, no unsaid recon. Fix the key.

<!-- /pigeon:hooks -->
<!-- pigeon:active-template -->
## Active Template: /debug

*Auto-selected 2026-04-13 19:12 UTC Â· mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 43 | Del: 26% | Hes: 0.487
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Codes:** intent=`unknown` state=`focused` bl_wpm=51 bl_del=26%
**Voice:** Operator is semi-casual â€” use contractions, skip formalities, but keep technical precision.; Operator never capitalizes â€” you don't need to either in casual responses, but keep code accurate.

---

## Fragile Contracts

- break mid-cycle. I receive all cross-referenced data from u_pj and manage the injection lifecycle. If the surface object size balloons, my memory trac
- contract change, (2) node_memory key `'numeric_surface'` missing or None, (3) surface object
- break it immediately. **_tmp_probe_loop** orchestrates diagnostic probes, expecting probe modules to return a specific dict schema; a schema violation
- risks API leakage. **codebase_vitals** now feeds metrics into the scanner hardening, providing complexity scores and assuming file paths are absolute;
- BREAKING: Self-Healing Codebase Clears 15 Zombie Modules in Single Push**

## Codebase Clots (dead/bloated)

- `aim_utils`: orphan_no_importers, unused_exports:1
- `press_release_gen_constants_seq001_v001`: orphan_no_importers, unused_exports:1
- `adapter`: orphan_no_importers, unused_exports:1
- `query_memory`: dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory

## Overcap Files (split candidates)

- `git_plugin` (6050 tok)
- `module_identity` (3770 tok)
- `è°±å»ºf_mb_s007_v003_d0314_è§‚é‡ç®±é‡æ‹†_Î»D` (3640 tok)
- `profile_renderer` (3337 tok)
- `tc_sim` (3230 tok)
- `classify_bridge` (3143 tok)
- `ç®¡w_cpm_s020_v005_d0404_ç¼©åˆ†è¯_Î»NU_Î²oc` (3118 tok)
- `å±‚w_sl_s007_v003_d0317_è¯»å”¤ä»»_Î»Î ` (3109 tok)

<!-- /pigeon:active-template -->
<!-- pigeon:probe-resolutions -->
## Probe Resolutions

*2 resolved Â· 2026-04-18 00:19 UTC*

**Read these before editing the referenced modules:**

- **`query_memory`**: operator keeps query_memory as a clot â€” should it be split, deleted, or repurposed for probe history?
  - â†’ Codebase pattern: 260+ modules, all decomposed by pigeon compiler. Split is the convention. (conf=0.60, via organism_directive)

- **`query_memory`**: operator keeps query_memory as a clot â€” should it be split, deleted, or repurposed for probe history?
  - â†’ Operator deleted reference to 'delete' â€” likely intended: The operator was about to specify that the testing should occur after the initial fix has been applied.
---
They likely deleted it because the overall (conf=0.60, via unsaid_recon)

<!-- /pigeon:probe-resolutions -->
