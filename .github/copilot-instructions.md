# Copilot Instructions â€” keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-19 23:05 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: STALE — 187min old (max 10min)
  - Writer: `prompt_enricher (Gemini Flash)`
  - Last updated: 2026-04-19 19:59

- **`prompt-telemetry`**: STALE — 187min old (max 10min)
  - Writer: `prompt_journal._refresh_copilot_instructions`
  - Last updated: 2026-04-19T19:59:02

- **`learning-loop`**: BEHIND — 228 unprocessed entries, last ran 176h ago
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

*Enriched 2026-04-19 19:59 UTC · raw: "network load audit test"*

**COPILOT_QUERY: Execute a network load audit test on the current system. Specifically, analyze the `tracks_cognitive_load_per_module` and `re_audit_with_diff_across` modules to identify potential bottlenecks or performance regressions. Provide a report detailing network usage and any observed anomalies.**

UNSAID_RECONSTRUCTION: can you do like a network load audit test on how to run this program and how to audit the idea way for a developer to plug this system in --- the loop is getting close to close

INTERPRETED INTENT: The operator wants to perform a network performance test, likely to identify issues related to the system's cognitive load tracking or audit functionalities.
KEY FILES: tracks_cognitive_load_per_module, re_audit_with_diff_across
PRIOR ATTEMPTS: The operator previously attempted to phrase this as "can you do like a network load audit test on how" but struggled with phrasing the scope and intent, leading to multiple deletions.
WATCH OUT FOR: Copilot might provide a generic network test without focusing on the specific modules or the "audit" aspect, which has been a recurring theme.
OPERATOR SIGNAL: The repeated deletions and rephrasing around "how" and "audit" indicate the operator is trying to specify the *method* or *scope* of the network load test, moving towards a more defined "audit" rather than a simple "test."
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-19 23:05 UTC · 676 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 46.9 | Del: 26.5% | Hes: 0.496) · *[source: measured]*

**Prompt ms:** 262039, 33194, 18225, 91051, 28757 (avg 86653ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 28.5% (200 responses)*
- Failed on: ""
- Failed on: ""
- Failed on: ""

### Recent Work
- `d9b4ece` fix: reseal master_test sha after cleanup commit
- `1554a42` cleanup: remove 73 _tmp_ root files, add chat_composition_analyzer + prompt_recon
- `7ed3e32` fix: repair git_plugin sibling names + 74 broken __init__.py imports after pigeon rename
- `04e3f2c` feat: seed 69 plain-named code files into pigeon naming convention

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- (1) predictor.get_surface_tensor shape contract change
- (2) node_memory key `'numeric_surface'` missing or None
- (3) surface object

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_brain/ai_cognitive_log.py`
- [HIGH] over_hard_cap in `pigeon_brain/context_veins.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/__main__.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/存p_nm_s008_v001_d0325_读唤任_λB.py`
- [HIGH] over_hard_cap in `pigeon_brain/flow/存p_nm_s008_v003_d0328_读唤任_λR.py`

### Prompt Evolution
*This prompt has mutated 122x (186→1003 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 122 mutations scored*
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

*Auto-extracted 2026-04-19 19:59 UTC · 78 prompts analyzed · zero LLM calls · scoring active*

**Brevity:** 37.3 words/prompt | **Caps:** never | **Fragments:** 83% | **Questions:** 12% | **Directives:** 10%

**Voice directives (effectiveness-scored):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** t, s, a, e, i, to, d, the, r, n
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-04 03:59 UTC Â· zero LLM calls*

**1 week:** `infrastructure` (conf=high) â€” ~46 commits
**1 month:** `infrastructure` (conf=medium) â€” ~173 commits
**3 months:** `infrastructure` (conf=speculative) â€” themes: use, rephraser, can we find a way to s

**PM Directives:**
- Intent bifurcation: `infrastructure` dominant but `telemetry` emerging â€” watch for context switches mid-session.
- `self_heal` declining â€” operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `use`, `rephraser`, `can we find a way to s` â€” these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.
- Module focus cluster: `file_heat_map`, `import_rewriter`, `file_writer` â€” pre-load context from these modules when operator starts typing.

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

*Auto-generated 2026-04-17 20:30 UTC*

**Operator coaching:**
- You referenced ['prompt_enricher_seq024_v001', 'prompt_journal'] but copilot didn't touch them â€” be more explicit about expected changes.
- Copilot edit pressure is concentrated in cortex â€” narrower prompts may reduce retouch churn in that region.

**Agent coaching (for Copilot):**
- Touched ['__main__', 'audit_loops', 'git_plugin_main_orchestrator', 'master_test'] without operator reference â€” confirm intent before modifying unreferenced modules.
- Operator needed many prompts â€” respond with more complete implementations to reduce round-trips.
- Low sync score â€” operator intent and code output diverged. Ask clarifying questions earlier.

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

*Auto-updated 2026-04-19 - 676 message(s) in profile*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.9 | Del: 25.5% | Hes: 0.443

**Behavioral tunes for this session:**
- **abandoned** -> welcoming, direct - they re-approached after backing off
- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples
- Active hours: 0:00(30), 1:00(45), 2:00(12), 3:00(9), 4:00(21), 5:00(24), 6:00(15), 7:00(15), 8:00(12), 9:00(18), 10:00(49), 11:00(9), 12:00(15), 13:00(9), 14:00(21), 15:00(39), 16:00(30), 17:00(12), 18:00(15), 19:00(33), 20:00(21), 21:00(60), 22:00(99), 23:00(63)
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
  "updated_at": "2026-04-19T19:59:02.603605+00:00",
  "latest_prompt": {
    "session_n": 1,
    "ts": "2026-04-19T19:59:02.603605+00:00",
    "chars": 23,
    "preview": "network load audit test",
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
    "total_prompts": 754,
    "avg_wpm": 9.0,
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
*2026-04-04 Â· 263 modules Â· 5 touched Â· âœ“71% ~12% !15%*
*Format: glyph=name seq tokensÂ·stateÂ·intentÂ·bugs |last change*
*IM=import_tracer MA=manifest_writer NL=nl_parsers PL=planner PQ=pq_search_utils PR=press_release_gen_template_key_findings*
*Intent: FX=fix RN=rename RF=refactor SP=split TL=telemetry CP=compress VR=verify FT=feature CL=cleanup OT=other PI=pigeon_brain DY=dynamic_import GE=gemini_flash RE=rework_signal 88=8888_word DE=desc_upgrade ST=stage_78 MU=multi_line IM=import_rewriter WI=windows_max IN=intent_deletion FI=fire_full WP=wpm_outlier PU=push_narratives TA=task_queue P0=p0_p3 NU=numeric_surface*
*Bugs: hi=hardcoded_import de=dead_export dd=duplicate_docstring hc=high_coupling oc=over_hard_cap qn=query_noise*

**pigeon_brain** (42)
åž‹=models 1 424âœ“Â·PI
è¯»=execution_logger 2 1.6K~Â·CP
å›¾=graph_extractor 3 1.7Kâœ“Â·88 |8888 word backpropagation
æ=graph_heat_map 4 874âœ“Â·PI
çŽ¯æ£€=loop_detector 5 910âœ“Â·PI
ç¼©=failure_detector 6 1.0Kâœ“Â·PI
è§‚=observer_synthesis 7 1.5K!Â·CP
åŒ=dual_substrate 8 1.3K!Â·PI
ä»¤=cli 9 855!Â·PI
ä»¿=demo_sim 10 1.3K!Â·PI
é’©=trace_hook 11 959~Â·PI
æœ=live_server 12 2.5K!Â·88 |8888 word backpropagation
è·‘=traced_runner 13 855!Â·PI

**pigeon_brain/flow** (44)
åŒ…=context_packet 1 1.0Kâœ“Â·TL |flow engine context
å”¤=node_awakener 2 1.3K~Â·CP
æµ=flow_engine 3 1.3K!Â·TL |flow engine context
æ‹©=path_selector 4 1.4Kâœ“Â·TL |flow engine context
ä»»=task_writer 5 1.6K~Â·CP
è„‰è¿=vein_transport 6 965~Â·CP
é€†=backward 7 2.5K!Â·DY
é€†f_ba 7 2.5KÂ·NUÂ·oc
å­˜=node_memory 8 2.1Kâœ“Â·DY
é¢„=predictor 9 1.8Kâœ“Â·SP
åˆ†=dev_plan 10 1.5K!Â·DY
è¯=node_conversation 12 1.4K!Â·DY
å­¦=learning_loop 13 2.9K!Â·SP
ç®—=prediction_scorer 14 5.8K!Â·GE
ç®—f_ps 14 5.8KÂ·NUÂ·oc

  é€†â”” flow_log(1) loss_compute(2) tokenize(3) deepseek_analyze(4) backward_pass(5) [2.6K]
  å­¦â”” state_utils(1) journal_loader(2) prediction_cycle(3) single_cycle_helpers(4) single_cycle(5) catch_up(6) loop_helpers(7) main_loop(8) [3.3K]
  ç®—â”” constants(1) path_utils(2) data_loaders(3) scores_io(3) reality_loaders(4) module_extractor(5) edit_session_analyzer(6) rework_matcher(7) scoring_core(8) calibration(9) node_backfill(10) post_edit_scorer(11) post_commit_scorer(12) [5.1K]
  é¢„â”” confidence(3) trend_extractor(4) predictor(7) [1.8K]
**pigeon_compiler/bones** (5)
è§„=aim_utils 1 724âœ“Â·DE
è”=core_formatters 1 1.3Kâœ“Â·DE
NL=nl_parsers 1 1.8Kâœ“Â·DE
æ¸…å•=pq_manifest_utils 1 879âœ“Â·DE
PQ=pq_search_utils 1 3.3K~Â·DE

**pigeon_compiler/cut_executor** (12)
æž=plan_parser 1 371âœ“Â·VR
åˆ‡=source_slicer 2 486âœ“Â·VR
å†™=file_writer 3 783~Â·MU |multi line import
è¸ª=import_fixer 4 505âœ“Â·VR
MA=manifest_writer 5 448âœ“Â·VR
éªŒ=plan_validator 6 579~Â·VR
åˆå†™=init_writer 7 361âœ“Â·ST
è¯‘=func_decomposer 8 644!Â·ST
é‡æ‹†=resplit 9 841!Â·VR
é‡æ‹†=resplit_binpack 10 702!Â·VR
é‡æ‹†=resplit_helpers 11 501âœ“Â·VR
ç»‡=class_decomposer 13 2.0K!Â·ST

**pigeon_compiler/integrations** (1)
è°±=deepseek_adapter 1 1.2Kâœ“Â·ST

**pigeon_compiler/rename_engine** (26)
æ‰«=scanner 1 972âœ“Â·VR
PL=planner 2 1.4K~Â·CP
å¼•=import_rewriter 3 1.8K~Â·IM |import rewriter now
å¼•w_ir 3 1.9KÂ·FX
åŽ‹=executor 4 712âœ“Â·VR
å®¡=validator 5 921âœ“Â·VR
å®¡p_va 5 1.0KÂ·FX
æ”¹å=run_rename 6 1.4K!Â·CP
è°±å»º=manifest_builder 7 2.9K!Â·DE
æ­£=compliance 8 1.7K!Â·VR
è¿½=heal 9 2.0K!Â·CP
è¿½è·‘=run_heal 10 3.4K!Â·VR
è¿½è·‘f_ruhe 10 4.7KÂ·FXÂ·oc
ç‰Œ=nametag 11 4.1K!Â·CP
å†Œ=registry 12 2.1K!Â·CP
å†Œf_reg 12 3.2KÂ·VRÂ·oc

  æ­£â”” helpers(2) classify(3) recommend_wrapper(6) audit_decomposed(7) audit_wrapper(9) check_file(10) format_report(11) [2.9K]
  è¿½â”” orchestrator(5) [725]
  ç‰Œâ”” scan(8) [298]
  å†Œâ”” diff(6) [194]
**pigeon_compiler/rename_engine/å†Œf_reg_s012_v005_d0402_è¿½è·‘è°±æ¡¥å¤å®¡_Î»VR_Î²oc** (1)
å†Œf_reg_s012_v005_d0402_è¿½è·‘è°±æ¡¥å¤å®¡_Î»VR_Î²oc_registry_io 4 285Â·FT

**pigeon_compiler/runners** (9)
æµ‹ç¼–=run_compiler_test 7 594~Â·VR
æ·±åˆ’=run_deepseek_plans 8 587~Â·VR
é¸½çŽ¯=run_pigeon_loop 9 2.8K!Â·VR
å‡€æ‹†=run_clean_split 10 2.5K!Â·WI |windows max path
å‡€æ‹†=run_clean_split_helpers 11 566!Â·VR
å‡€æ‹†=run_clean_split_init 12 1.7K~Â·VR
è°±æ¡¥=manifest_bridge 13 1.0Kâœ“Â·VR
å¤å®¡=reaudit_diff 14 1.7Kâœ“Â·VR
æ‰¹ç¼–=run_batch_compile 15 2.0K!Â·DY

**pigeon_compiler/runners/compiler_output/press_release_gen** (8)
press_release_gen_constants_seq001_v001 1 641âœ“Â·VR
press_release_gen_template_builders_seq002_v001 1 626âœ“Â·VR
press_release_gen_template_helpers_seq004_v001 1 661âœ“Â·VR
press_release_gen_constants_seq001_v001 2 388âœ“Â·VR
press_release_gen_template_builders_seq002_v001 2 662âœ“Â·VR
press_release_gen_template_helpers_seq004_v001 2 296âœ“Â·VR
press_release_gen_template_builders_seq002_v001 3 296âœ“Â·VR
PR=press_release_gen_template_key_findings 3 626âœ“Â·VR

**pigeon_compiler/state_extractor** (6)
æŸ¥=ast_parser 1 734âœ“Â·VR
æ¼”=call_graph 2 847âœ“Â·VR
IM=import_tracer 3 792âœ“Â·VR
å…±æ€=shared_state_detector 4 618âœ“Â·VR
é˜»=resistance_analyzer 5 1.0K~Â·VR
æ‹†=ether_map_builder 6 697!Â·VR

**pigeon_compiler/weakness_planner** (1)
æ ¸=deepseek_plan_prompt 4 2.4K~Â·DE

**src** (113)
æ—¶=timestamp_utils 1 156âœ“Â·RN |test rename hook
åž‹=models 2 379âœ“Â·TL |pulse telemetry prompt
å½•=logger 3 1.6Kâœ“Â·WP |wpm outlier filter
å¢ƒ=context_budget 4 715~Â·FI |test full hook
å=drift_watcher 5 1.1Kâœ“Â·FT
æ¡¥=resistance_bridge 6 1.2Kâœ“Â·TL |pulse telemetry prompt
å±‚=streaming_layer 7 10.2K~Â·TL |pulse telemetry prompt
æ¼‚=.operator_stats 8 4.7K~Â·IN |intent deletion pipeline
æŽ§=operator_stats 8 5.0K!Â·WP |fix degenerate classifier:
æµ‹=rework_detector 9 1.1Kâœ“Â·FT |add composition-based scoring,
æµ‹p_rwd 9 1.8KÂ·P0Â·de
å¿†=query_memory 10 2.3Kâœ“Â·FT
çƒ­=file_heat_map 11 1.3Kâœ“Â·TL |pulse telemetry prompt
çƒ­p_fhm 11 1.7KÂ·P0Â·de
å™=push_narrative 12 2.1Kâœ“Â·PU |push narratives timeout
å™p_pn 12 2.1KÂ·P0
ä¿®=self_fix 13 5.8K!Â·DY
ä¿®f_sf 13 5.8KÂ·VRÂ·oc
æ€=cognitive_reactor 14 5.6K!Â·MU |mutation patch pipeline
è„‰=pulse_harvest 15 2.3Kâœ“Â·FT
è„‰p_ph 15 2.4KÂ·P0Â·oc
æŽ¨=dynamic_prompt 17 4.0K~Â·88 |8888 word backpropagation
æŽ¨w_dp 17 6.0KÂ·P0Â·oc
é˜Ÿ=task_queue 18 1.6Kâœ“Â·TA |task queue system
è§‰=file_consciousness 19 4.3K~Â·FT
u_pj 19 7.9KÂ·NUÂ·oc
ç®¡=copilot_prompt_manager 20 4.5K~Â·FT |resolve latest runtime
ç®¡w_cpm 20 8.0KÂ·NUÂ·oc
å˜=mutation_scorer 21 1.6Kâœ“Â·FT
è¡¥=rework_backfill 22 1.2Kâœ“Â·FT
é€’=session_handoff 23 1.6Kâœ“Â·FT
u_pe 24 5.1KÂ·P0Â·oc |add bug dossier
éš=unsaid_recon 24 1.3Kâœ“Â·IN |intent deletion pipeline
çŽ¯=push_cycle 25 4.8K~Â·FX |fix push cycle
ç‰‡=shard_manager 26 4.4K~Â·GE
åˆ=unified_signal 26 2.1Kâœ“Â·GE
è·¯=context_router 27 1.2K!Â·GE
å¯¹=training_pairs 27 2.6Kâœ“Â·GE
å¯¹p_tp 27 3.8KÂ·VRÂ·oc
è®­=training_writer 28 2.1K~Â·GE
å£°=voice_style 28 3.2K~Â·GE
ç ”=research_lab 29 5.1K~Â·SP |rewrite in intent
è­¦=staleness_alert 30 1.7Kâœ“Â·ST |staleness alerts bg
è­¦p_sa 30 1.8KÂ·CPÂ·oc |test rename mutation
å…¸=symbol_dictionary 31 3.7K~Â·SP |swap to chinese
ç¼–=glyph_compiler 32 5.0K~Â·SP |glyph compiler symbol
intent_simulator 34 5.3KÂ·CP |compress auto index

**src/cognitive** (10)
é€‚=adapter 1 1.3Kâœ“Â·VR
éš=unsaid 2 2.1Kâœ“Â·VR
å=drift 3 2.3Kâœ“Â·VR

  åâ”” baseline_store(1) compute_baseline(2) detect_session_drift(3) build_cognitive_context(4) [2.4K]
  éšâ”” helpers(1) diff(2) orchestrator(3) [2.3K]
  æ€â”” constants(1) state_ops(2) docstring_patch(3) cognitive_hint(4) patch_generator(5) prompt_builder(6) api_client(7) reactor_core(8) registry_loader(9) self_fix_runner(10) patch_writer(11) decision_maker(12) [4.9K]
  ç®¡â”” constants(1) block_utils(2) json_utils(3) operator_profile(4) auto_index(5) operator_state_decomposed(6) telemetry_utils(7) audit_decomposed(8) injectors(9) orchestrator(10) [4.6K]
  è§‰â”” helpers(1) persistence(2) report(3) audit(4) derivation(5) dependencies(6) classify(7) profile_builder(8) main_orchestrator(9) dating_decomposed(10) dating_helpers(11) dating_wrapper(12) [5.0K]
  çŽ¯â”” constants(1) loaders(2) signal_extractors(3) sync_decomposed(4) coaching(5) moon_cycle(6) predictions_injector_decomposed(7) orchestrator_decomposed(8) [4.5K]
  å¿†â”” constants(1) fingerprint(2) trigram_utils(3) clustering(4) record_query(5) load_memory_decomposed(6) [1.4K]
  ä¿®â”” scan_hardcoded(1) scan_query_noise(2) scan_duplicate_docstrings(3) scan_cross_file_coupling(4) scan_over_hard_cap_decomposed(5) scan_dead_exports_decomposed(6) write_report_decomposed(7) run_self_fix_decomposed(8) auto_compile_oversized_decomposed(9) seq_base(10) auto_apply_import_fixes_decomposed(11) [6.0K]
**src/ä¿®_sf_s013** (1)
ä¿®f_sf_aco 9 857Â·VR

**src/ç®¡w_cpm_s020_v003_d0402_ç¼©åˆ†è¯_Î»VR_Î²oc** (1)
ç®¡w_cpm_s020_v003_d0402_ç¼©åˆ†è¯_Î»VR_Î²oc_refresh_decomposed 10 701Â·P0

**streaming_layer** (19)
å±‚=streaming_layer_constants 1 261âœ“Â·VR
å±‚=streaming_layer_simulation_helpers 2 204âœ“Â·VR
å±‚=streaming_layer_dataclasses 4 717âœ“Â·VR
å±‚=streaming_layer_formatter 4 546âœ“Â·VR
å±‚=streaming_layer_connection_pool 5 969!Â·DY
å±‚=streaming_layer_dataclasses 5 247âœ“Â·VR
å±‚=streaming_layer_aggregator 6 934!Â·DY
å±‚=streaming_layer_dataclasses 6 154âœ“Â·VR
å±‚=streaming_layer_metrics 7 824~Â·DY
å±‚=streaming_layer_alerts 8 1.4K!Â·DY
å±‚=streaming_layer_replay 9 932âœ“Â·VR
å±‚=streaming_layer_dashboard 10 858âœ“Â·DY
å±‚=streaming_layer_http_handler 11 1.2K~Â·DY
å±‚=streaming_layer_demo_functions 13 456âœ“Â·VR
å±‚=streaming_layer_demo_summary 13 365âœ“Â·VR
å±‚=streaming_layer_demo_functions 14 280âœ“Â·VR
å±‚=streaming_layer_demo_simulate 14 256âœ“Â·VR
å±‚=streaming_layer_orchestrator 16 1.4K!Â·DY
å±‚=streaming_layer_orchestrator 17 142!Â·VR

**Infra**
(root): _audit_compliance, _build_organism_health, _export_dev_story, _fix_stale_globs, _run_abbrev_rename, _run_glyph_rename, _run_smart_rename, _tmp_analyze_stats, _tmp_backfill_lastchange, _tmp_bug_audit, _tmp_check_rename, _tmp_find_stale, _tmp_regen_dict, _tmp_survey, _tmp_test_dossier, _tmp_test_pipeline, _tmp_test_surface, _tmp_token_audit, autonomous_dev_stress_test, deep_test, stress_test, test_all, test_public_release, test_training_pairs
client: chat_composition_analyzer, chat_response_reader, composition_recon, os_hook, telemetry_cleanup, uia_reader, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
<!-- pigeon:bug-voices -->
## Bug Voices

*Persistent bug demons minted from registry scars - active filename bugs first.*

- `ai_cognitive_log` d0418v000 · oc `Overcap Maw of aicognit` x1 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `entropy_shedding` d0418v000 · oc `Overcap Maw of entropys` x1 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `gemini_chat` d0418v000 · oc `Split Fiend of geminich` x1 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `node_tester` d0418v000 · oc `Split Fiend of nodetest` x1 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
- `tc_context` d0418v000 · oc `Shard Hunger of tccontex` x1 other=hc: "I keep swelling this file past the hard cap. Split me before I eat context."
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
