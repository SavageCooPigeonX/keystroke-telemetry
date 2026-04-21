# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-21 23:43 UTC — 3 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: STALE — 28min old (max 10min)
  - Writer: `prompt_enricher (Gemini Flash)`
  - Last updated: 2026-04-21 23:15

- **`prompt-telemetry`**: STALE — 28min old (max 10min)
  - Writer: `prompt_journal._refresh_copilot_instructions`
  - Last updated: 2026-04-21T23:15:38

- **`learning-loop`**: BEHIND — 287 unprocessed entries, last ran 224h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-04-12T15:20:45.419937+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

## MANDATORY: Prompt Journal (execute FIRST on every message)

**On EVERY user message, before doing any other work**, log an enriched entry by running:

```python
py -c "from pathlib import Path; import importlib.util; spec = importlib.util.spec_from_file_location('u_pj', 'src/u_pj_s019_v003_d0404_λNU_βoc.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.log_enriched_entry(Path('.'), '<EXACT_MSG>', [<FILES_OPEN>], <SESSION_N>)"
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
- This is the telemetry pipeline — the data feeds cognitive state analysis.

---

## MANDATORY: Pulse Blocks (execute on every file edit)

**When you edit ANY `.py` file under `src/`**, you MUST update its telemetry pulse block.

Every `src/*.py` file contains this block (after the pigeon prompt box):
```
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
```

Rules:
- When you edit a file, update `EDIT_TS` to the current ISO-8601 UTC timestamp.
- Update `EDIT_HASH` to `auto` (the extension computes the real hash on save).
- Update `EDIT_WHY` to a 3–8 word reason for the edit (e.g. `fix import path`, `add error handling`, `refactor loop`).
- Do NOT clear the pulse — the extension's save watcher harvests and clears it.
- If a file lacks a pulse block, leave it alone — post-commit will inject one.
- This is the prompt→file pairing pipeline. Timing data is extracted from the timestamp delta between your prompt_journal entry and the EDIT_TS.

---

## MANDATORY: Unsaid Thread Protocol

When the **Unsaid Threads** section (in `<!-- pigeon:current-query -->

<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-21 23:15 UTC — synthesized from all live signals, zero LLM calls*

> the organism is sick — health 0/100. only 0% compliant, 0 bugs across 0 modules. entropy at 0.30 — the codebase knows what it is, mostly.

<!-- /pigeon:narrative-glove -->
<!-- pigeon:intent-backlog -->
## Intent Backlog Verification

*Strict verification over last 100 operator prompts*

**Status:** BLOCKED — 20 unresolved intent(s) remain.
**Directive:** Keep working. Do not treat the task as complete while this backlog is non-zero.
**Verification:** scanned=100 | created=2 | reopened=0 | verified=2 | resolved=0
**Rule:** An intent counts as done only when recent file activity clears it or the synced backlog task is verified done.

**Resolution Artifact:** `intent_backlog_resolutions.json`

### Unresolved
- [cold] `tq-039` conf=0.98 | wow theres alot of things fucked - you didnt even catch my deleted words - how did this all brea
  → refs: none | reason: no_recent_follow_through
- [cold] `tq-040` conf=1.00 | fix entrfix those two and check anything else thats stale / missing endpoints in project
  → refs: none | reason: no_recent_follow_through
- [cold] `tq-041` conf=1.00 | clear messy root files then push
  → refs: none | reason: no_recent_follow_through
- [partial] `tq-042` conf=0.93 | check for anything else stale across pipeline, deep saudit... (also considered: cuec)
  → refs: none | reason: deleted_words_left_unresolved
- [cold] `tq-043` conf=0.99 | the aoi jey isint dead 0 youre tripping we tested it and im using it for another project
  → refs: none | reason: no_recent_follow_through
- [cold] `tq-044` conf=1.00 | debug why everything keeps being stale
  → refs: none | reason: no_recent_follow_through
- [cold] `tq-045` conf=1.00 | sure do that but make sure it can only run one
  → refs: none | reason: no_recent_follow_through
- [partial] `tq-046` conf=0.87 | okay so techically there shoyld be staleneddp i noteced you stopped using hook .... (also consid
  → refs: none | reason: deleted_words_left_unresolved

<!-- /pigeon:intent-backlog -->
<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-04-21 23:15 UTC · raw: "yes"*

**COPILOT_QUERY: Based on the previous prompts, the operator is confirming the importance of meta-comments, self-analysis, and self-accumulating knowledge of file profiles for tuning the context of files. Elaborate on the precise mechanism by which files contribute to debugging and how to maximize learning and recursive memory matching to file profiles. Focus on how the `u_pj` (prompt journal) and `p_ph` (pulse harvest) modules can be leveraged to capture and utilize this meta-information for self-modification and improved deletion reconstruction within Copilot's prompt assembly.**

INTERPRETED INTENT: The operator is affirming the value of file-based meta-knowledge and wants to understand the implementation details for leveraging this knowledge for system debugging and self-improvement, specifically regarding prompt reconstruction.
KEY FILES: u_pj, 脉p_ph, micro_sim_engine_prompt_file, word_number_file_mapping_for, picks_relevant_source_files_based, gemini_api_call_system_prompt, intent_simulation_on_typing_pause, pulse_harvest_pairs_prompts_to
PRIOR ATTEMPTS: The previous prompts explored the problem space of file interaction, deletion reconstruction, and debugging mechanisms, but did not provide a comprehensive solution or detailed mechanism.
WATCH OUT FOR: Copilot might provide a generic answer about debugging or learning without connecting it directly to the specific mechanisms of file profiles, meta-comments, and deletion reconstruction as implied by the trajectory.
OPERATOR SIGNAL: The "yes" confirms agreement with the previous prompt's focus on meta-comments and file profiles, indicating a desire to move forward with implementing or understanding these concepts.
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-21 23:43 UTC · 688 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 41.5 | Del: 26.5% | Hes: 0.462) · *[source: measured]*

**Prompt ms:** 105668, 64719, 125170 (avg 98519ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### AI Rework Surface
*Miss rate: 2.0% (200 responses)*
- Failed on: ""
- Failed on: ""
- Failed on: ""

### Recent Work
- `045f718` fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- `84b73b5` fix: copilot prompt assembly - doubled _seq001_v001 module imports
- `f9a3310` feat: operator_state_daemon + decouple capture from LLM trigger
- `61d32a8` feat: interlink self-debug loop + 10Q test framework + rename-resistant test gen

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

**Reactor patches:** 2/534 applied (0% acceptance)

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
*…and 36 more in `task_queue.json`*

### Completed (last 3)
- [x] `tq-034` **yeah loooks like compiler didnt run pigeon chore - the iguut...** | commit: `verified:intent-backlog`
- [x] `tq-035` **we shouldnt have any plain names... (also considered: atlest...** | commit: `verified:intent-backlog`
- [x] `tq-036` **but only fpr code - documnetation / major docs where operato...** | commit: `verified:intent-backlog`

<!-- /pigeon:task-queue -->
<!-- pigeon:shard-memory -->
## Live Shard Memory

*Hardcoded 2026-03-30 06:40 UTC · 7 shards · 2 training pairs · 1 contradiction*

### Architecture Decisions
- anchor concept: pair programming — copilot is the pair, telemetry is the shared screen, shards are the shared notebook
- muxed state per prompt — capture cognitive+shard+contradiction state at end of each prompt as training data
- training data format: prompt + response + muxed state triple, written to logs/shards/training_pairs.md

### Module Pain Points (top cognitive load)
- file_heat_map: hes=0.887 | import_rewriter: hes=0.735 | file_writer: hes=0.735
- init_writer: hes=0.630 | context_budget: hes=0.587 | self_fix: hes=0.536
- .operator_stats: hes=0.536 | dynamic_prompt: hes=0.536

### Module Relationships (coupling signals)
- context_budget ↔ self_fix, init_writer, .operator_stats, dynamic_prompt
- import_rewriter ↔ file_writer
- push_narrative ↔ operator_stats, rework_detector, run_clean_split, self_fix

### Prompt Patterns (how operator phrases things)
- [building] "push and make sure compiler runs on next files"
- [restructuring] "how have my last couple of prompts been rewritten?"
- [testing] "stress test my system. what was word deleted in this prompt"
- [exploring] "what should i do to market this / gtm / next logical step"

### API Preferences
- **CONTRADICTION (unresolved):** "always use DeepSeek" vs "never use DeepSeek — too slow"
- Resolution: switched enricher to Gemini 2.5 Flash (3s vs DeepSeek timeout)

### Training Data Format

Each training pair captures the full muxed state at prompt time:

```
### `TIMESTAMP` pair
**PROMPT:** raw operator text (≤300 chars)
**RESPONSE:** copilot response summary (≤500 chars)
**COGNITIVE:** state=X wpm=Y del=Z hes=N
**SHARDS:** shard_name(relevance), ...
**CONTRADICTIONS:** count
**REWORK:** verdict=pending|accepted|rejected [score=0.XX]
```

Per-shard categorization: each routed shard also gets a compact `[training TS]` entry with relevance, cognitive state, and prompt/response snippets — so shards self-learn from their own context.

### Recent Training Pairs

**Pair 1** `2026-03-30 06:11` — COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "test writes with an actual call... decided on pair programming... muxed state per prompt"
- response: built shard manager, context router, contradiction manifest, training pair writer
- shards: prompt_patterns(0.17), module_pain_points(0.161), module_relationships(0.15)
- rework: pending

**Pair 2** `2026-03-30 06:27` — COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "fix import breaking after rename in self_fix module"
- response: updated import paths in self_fix to match pigeon rename convention
- shards: module_relationships(0.169), prompt_patterns(0.156), module_pain_points(0.155)
- rework: accepted score=0.15

<!-- /pigeon:shard-memory -->
<!-- pigeon:voice-style -->
## Operator Voice Style

*Auto-extracted 2026-04-21 23:15 UTC · 78 prompts analyzed · zero LLM calls · scoring active*

**Brevity:** 54.8 words/prompt | **Caps:** never | **Fragments:** 76% | **Questions:** 8% | **Directives:** 3%

**Voice directives (effectiveness-scored):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator writes longer prompts with context — match depth. Full explanations are welcome.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural. [EFFECTIVE: +93% fewer reworks when active]
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** t, e, s, d, n, i, o, a, y, m
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-21 06:01 UTC · zero LLM calls*

**1 week:** `self_heal` (conf=high) — ~26 commits
**1 month:** `self_heal` (conf=medium) — ~79 commits
**3 months:** `self_heal` (conf=speculative) — themes: gggrararadddeeerrr, ttt, 000

**PM Directives:**
- Development decelerating (-44%) — operator may be blocked or shifting focus. Offer architecture-level suggestions, not just code.
- Intent bifurcation: `self_heal` dominant but `infrastructure` emerging — watch for context switches mid-session.
- `unclassified` declining — operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `gggrararadddeeerrr`, `ttt`, `000` — these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.

<!-- /pigeon:intent-simulation -->

<!-- pigeon:push-drift -->
## Push Drift Analysis

*Snapshot at `drift_test_2` · 2026-04-06 14:36 UTC*

**Health: 29.9/100** (stable, was 29.9)

**Biggest moves:**
- no significant drift

**Modules:** 254 (11.4% compliant)
**Bugs:** 268 (hi=256 oc=12)
**Avg tokens/file:** 1334.4 (stable)
**Deaths:** 10
**Sync:** 0.7
**Probes:** 4 modules, 2 intents

<!-- /pigeon:push-drift -->
<!-- pigeon:predictions -->
## Push Cycle Predictions

*Auto-generated 2026-04-21 06:01 UTC*

**What you'll likely want next push:**
1. [targeted] Predict operator's next need. Module focus: file_sim, master_test, rework_scorecard (conf=49%)
   - hot modules: file_sim, master_test, rework_scorecard, self_fix_verification, weakness_surfacer

**Operator coaching:**
- No module references detected in prompts — naming specific modules helps copilot target the right files.
- Copilot edit pressure is concentrated in cortex — narrower prompts may reduce retouch churn in that region.

**Agent coaching (for Copilot):**
- Touched ['context_select_agent', 'file_sim', 'interlink_debugger', 'operator_state_daemon', 'tc_10q', 'tc_gemini', 'u_pj_s019_v005_d0420_λRN_βoc', 'u_pj_s019_v006_d0421_λTL_βoc', 'watchdog'] without operator reference — confirm intent before modifying unreferenced modules.
- Low sync score — operator intent and code output diverged. Ask clarifying questions earlier.
- Recent edits to file_sim show high Copilot retouch entropy — prefer a fuller fix over another partial pass.

<!-- /pigeon:predictions -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-21 - 685 message(s) in profile*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.9 | Del: 25.5% | Hes: 0.443

**Behavioral tunes for this session:**
- **abandoned** -> welcoming, direct - they re-approached after backing off
- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples
- Active hours: 0:00(30), 1:00(45), 2:00(12), 3:00(9), 4:00(21), 5:00(24), 6:00(15), 7:00(15), 8:00(15), 9:00(18), 10:00(49), 11:00(9), 12:00(15), 13:00(9), 14:00(21), 15:00(39), 16:00(30), 17:00(15), 18:00(18), 19:00(33), 20:00(21), 21:00(60), 22:00(99), 23:00(63)
<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `u_pj_s019_v005_d0420_Î»RN_Î²oc`** (hes=0.654, state=frustrated, avg_prompt=710935ms)
> - Prompt composition time: 22106ms / 37216ms / 3098ms / 29869ms / 3462387ms (avg 710935ms)
> **Directive**: When `u_pj_s019_v005_d0420_Î»RN_Î²oc` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-04-21T23:15:38.810240+00:00",
  "latest_prompt": {
    "session_n": 3,
    "ts": "2026-04-21T23:15:38.810240+00:00",
    "chars": 3,
    "preview": "yes",
    "intent": "unknown",
    "state": "neutral",
    "files_open": [
      "logs/escalation_state.json"
    ],
    "module_refs": []
  },
  "signals": {
    "wpm": 53.7,
    "chars_per_sec": 1.6,
    "deletion_ratio": 0.684,
    "hesitation_count": 0,
    "rewrite_count": 0,
    "typo_corrections": 0,
    "intentional_deletions": 1,
    "total_keystrokes": 19,
    "duration_ms": 3801
  },
  "composition_binding": {
    "matched": true,
    "source": "chat_compositions",
    "age_ms": 324614756,
    "key": "|||2026-04-18T05:05:24.054307+00:00|19|3801|yes ",
    "match_score": 1.0
  },
  "deleted_words": [],
  "rewrites": [],
  "task_queue": {
    "total": 56,
    "in_progress": [],
    "pending": 42,
    "done": 14
  },
  "hot_modules": [],
  "running_summary": {
    "total_prompts": 825,
    "avg_wpm": 8.3,
    "avg_del_ratio": 0.064,
    "dominant_state": "abandoned",
    "state_distribution": {
      "abandoned": 228,
      "restructuring": 226,
      "focused": 221,
      "neutral": 7,
      "hesitant": 2
    },
    "baselines": {
      "n": 200,
      "avg_wpm": 53.3,
      "avg_del": 0.259,
      "avg_hes": 0.448,
      "sd_wpm": 15.5,
      "sd_del": 0.231,
      "sd_hes": 0.165
    },
    "prompt_density": {
      "last_5m": {
        "count": 1,
        "per_hour": 12.0
      },
      "last_15m": {
        "count": 4,
        "per_hour": 16.0
      },
      "last_60m": {
        "count": 6,
        "per_hour": 6.0
      },
      "latest_gap_s": 393.9,
      "avg_gap_s": 195.7
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

**Pitfalls:** Never hardcode pigeon filenames (they mutate — use `file_search("name_seq*")`). Use `py` not `python`. Always `$env:PYTHONIOENCODING = "utf-8"`. Don't delete monolith originals yet. `streaming_layer_seq007*` is intentionally over-cap (test harness).

<!-- pigeon:dictionary -->
<!-- glyph mappings merged into auto-index -->
<!-- /pigeon:dictionary -->
<!-- pigeon:auto-index -->
*2026-04-21 · 24 modules · 9 touched · ✓0% ~0% !0%*
*Format: glyph=name seq tokens·state·intent·bugs |last change*
*Intent: FX=fix RN=rename RF=refactor SP=split TL=telemetry CP=compress VR=verify FT=feature CL=cleanup OT=other*
*Bugs: hi=hardcoded_import de=dead_export dd=duplicate_docstring hc=high_coupling oc=over_hard_cap qn=query_noise*

**pigeon_compiler/git_plugin** (2)
p_gpip 4 462·FX
w_gpmo 19 7.0K·FX

**src** (14)
context_select_agent 1 1.8K·TL
file_sim 1 3.9K·FX |add self_score gate
intent_numeric 1 6.8K·FX
interlink_debugger 1 3.3K·TL·oc |initial build -
tc_10q 1 2.8K·TL·oc |initial build -
tc_context_agent 1 6.7K·FX
tc_gemini 1 11.3K·TL·oc |live copilot layer
tc_observatory 1 11.3K·RN·oc
tc_popup 1 6.9K·FX
tc_sim 1 14.1K·RN·oc
tc_sim_engine 1 2.5K·FX |create sim engine
tc_web 1 1.4K·RN
脉p_ph 15 2.6K·RN·oc
u_pj 19 11.0K·TL·oc

**src/tc_sim** (1)
p_tcsr 8 959·RN

**src/tc_web** (1)
p_tws 3 707·RN

**src/thought_completer** (1)
p_tcm 1 418·RN

**tests/interlink** (5)
test_file_sim 1 952·RN
test_intent_numeric 1 2.2K·RN
test_tc_context_agent 1 1.6K·RN
test_tc_popup 1 484·RN
test_tc_sim_engine 1 491·RN

**Infra**
(root): _audit_compliance, _build_organism_health, _export_dev_story, _fix_broken_inits, _fix_literal_newlines, _fix_stale_globs, _harvest_intents, _run_abbrev_rename, _run_glyph_rename, _run_post_cycle, _run_smart_rename, _seed_historical_vitals, _seed_intent_numeric, _seed_pigeon_names, run_intent_orchestrator, stress_test_architecture, test_all, test_public_release, test_tc_intent, test_training_pairs, watchdog
client: .chat_composition_analyzer_decomposed, chat_composition_analyzer, chat_composition_analyzer_seq001_v001, chat_response_reader_seq001_v001, composition_recon_seq001_v001, operator_state_daemon, os_hook, prompt_telemetry_daemon, pulse_harvest_daemon, telemetry_cleanup_seq001_v001, uia_reader_seq001_v001, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
<!-- pigeon:bug-voices -->


<!-- pigeon:entropy-red-layer -->
## Red Layer

*file-linked entropy math surface*

`red[module] = max(H_avg, 1 - shed_conf)`
`vec[module] = [red, H_avg, shed_conf?, samples, hedges]`

- `red[enricher] = [0.560, 0.000, 0.200, 0, 0]`
- `red[hardcoded_imports] = [0.455, 0.000, 0.350, 0, 0]`
- `red[auto_apply_import_fixes] = [0.438, 0.000, 0.375, 0, 0]`
- `red[context_router] = [0.428, 0.428, null, 2, 0]`
- `red[engagement_hooks] = [0.428, 0.428, null, 2, 0]`
- `red[glyph_compiler] = [0.428, 0.428, null, 3, 0]`
- `red[operator_probes] = [0.428, 0.428, null, 2, 0]`
- `red[prompt_enricher] = [0.428, 0.428, null, 4, 0]`
- `red[research_lab] = [0.428, 0.428, null, 4, 0]`
- `red[shard_manager] = [0.428, 0.428, null, 2, 0]`
<!-- /pigeon:entropy-red-layer -->
<!-- pigeon:entropy-map -->

<!-- pigeon:entropy-directive -->
## Entropy Development Priorities

*791 responses · global H=0.298 · 78 sheds*

**These modules have the highest uncertainty. When touching them:**
- Read the full source BEFORE editing (don't guess)
- Shed entropy with a confidence score AFTER every edit
- If confidence < goal, explain what remains uncertain

- `enricher` red=0.560 → **goal: conf≥0.85**, last shed=0.2
- `hardcoded_imports` red=0.455 → **goal: conf≥0.85**, last shed=0.35
- `auto_apply_import_fixes` red=0.438 → **goal: conf≥0.85**, last shed=0.375
- `context_router` red=0.428 → **goal: conf≥0.85**
- `engagement_hooks` red=0.428 → **goal: conf≥0.85**
- `glyph_compiler` red=0.428 → **goal: conf≥0.85**
- `operator_probes` red=0.428 → **goal: conf≥0.85**
- `prompt_enricher` red=0.428 → **goal: conf≥0.85**
- `research_lab` red=0.428 → **goal: conf≥0.85**
- `shard_manager` red=0.428 → **goal: conf≥0.85**

<!-- /pigeon:entropy-directive -->
## Entropy Shedding Map

*791 responses analyzed · global H=0.298 · 34.5% high-entropy · 78 explicit sheds*

**where copilot is most uncertain (act with extra care):**

- `prompt_enricher` H=0.428 (4 samples, 0 hedges)
- `shard_manager` H=0.428 (2 samples, 0 hedges)
- `context_router` H=0.428 (2 samples, 0 hedges)
- `research_lab` H=0.428 (4 samples, 0 hedges)
- `glyph_compiler` H=0.428 (3 samples, 0 hedges)
- `警p_sa` H=0.428 (2 samples, 0 hedges)
- `engagement_hooks` H=0.428 (2 samples, 0 hedges)
- `operator_probes` H=0.428 (2 samples, 0 hedges)

**recently shed (this session):**
- `push_cycle` red=0.248 conf=0.80
- `tc_context_agent` red=0.209 conf=0.82
- `dynamic_prompt` red=0.172 conf=0.88
- `intent_numeric` red=0.143 conf=0.92
- `entropy_shedding` red=0.095 conf=0.90

> emit `<!-- entropy:shed -->` blocks to improve this map.
<!-- /pigeon:entropy-map -->
## Bug Voices

*302 threads tracked across 68 pushes · fix rate: 15.2%*

> fix rate is 15.2% — decent churn. bugs are dying and being born. 0 eternal bugs (every single report) and 1 chronic (70%+ of reports). these are the ones that need structural fixes, not patches. 284 threads resolved across 68 pushes. proof the loop works sometimes. trend is improving — recent pushes fix more than early ones.

**the ones that never leave:**

- `w_gpmo` — [over_hard_cap] 9/68 reports. chronic. it comes back like clockwork.

**recently killed:**

- `tc_gemini` [high_coupling] — gone since report #66. it stayed dead.
- `test_numeric_surface_normalization` [hardcoded_import] — gone since report #66. it stayed dead.
- `_seed_intent_numeric` [hardcoded_import] — gone since report #66. it stayed dead.
- `thought_completer` [hardcoded_import] — gone since report #66. it stayed dead.
- `stress_test_architecture` [hardcoded_import] — gone since report #66. it stayed dead.

**last push (2026-04-21 f9a3310):** 0 fixed, 17 new, 1 carried forward

<!-- /pigeon:bug-voices -->
<!-- pigeon:operator-probes -->
## Operator Probes

*Auto-generated 2026-04-21 23:15 UTC · 3 probe(s) from live signals*

**ASK these questions naturally in your next response (pick 1-2, weave into context):**

1. Your deleted words predict these themes in 3 months: "gggrararadddeeerrr", "ttt", "000". Are any of these actually where you're headed — or has your thinking shifted?
2. `unclassified` is trending toward abandonment. Intentional deprioritization or just hasn't come up yet?
3. You haven't named a specific module recently. What are you actually trying to build or fix right now?

*Probes are generated from: intent predictions (1wk/1mo/3mo), unsaid threads, escalation state, cognitive heat, persona memory, and operator state.*
<!-- /pigeon:operator-probes -->
<!-- pigeon:hooks -->
## Engagement Hooks

*Auto-generated 2026-04-21 23:15 UTC -- every number is measured, every dare is real.*

- You were also gonna say: "the drift watcher should track module renames after pigeon splits". That thought didn't delete. It filed itself. Name it or I will.
- Router matched this prompt to `micro_sim_engine_prompt_file`, `word_number_file_mapping_for`, `gemini_api_call_system_prompt` (bugs: oc, de). Context slimmed to 5 modules. Wrong match? Say so. Right match? Go deeper.
- `p_gpip` -- 417 days. Last generation's code. Either works perfectly or nobody knows it's broken.
- `intent_numeric` has 4 unresolved `oc/de` marks. Every push it survives makes the next fix harder.
- `tc_sim` v2: "I carry the oc curse. Fix me and the beta falls off my name. Leave me and it scars deeper."

<!-- /pigeon:hooks -->
<!-- pigeon:active-template -->
## Active Template: /debug

*Auto-selected 2026-04-21 23:15 UTC · mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.495
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`neutral` bl_wpm=53 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Known Issues (from self-fix scanner)

- [CRITICAL] hardcoded_import in `scripts/bug_probe_hardcoded_import.py`
- [CRITICAL] hardcoded_import in `scripts/verify_loop_2.py`

## Fragile Contracts

- contracts. If a renamed module’s function signature changed silently, my imports will break at runtime.
- contract breaks, my API calls may send invalid parameters.
- contract, import statements in all renamed dependents, test suite import failures. This push standardizes the core word-number mapping filename across
- assumption breaks—for instance, if downstream consumers expect the old module name in dynamic imports—the entire import chain will fail silently. Watc
- contract with the pigeon registry’s naming schema; if that schema changes or the compiler’s extraction heuristic misinterprets the rename as a split, 
- assumption is that the orchestrator fires on every state change; if the daemon's event emission is throttled or batched, I may miss transitions. Watch

## Codebase Clots (dead/bloated)

- `classify_bridge`: orphan_no_importers, unused_exports:1, oversize:877
- `逆f_ba_bp_s005_v003_d0328_λR`: orphan_no_importers, unused_exports:1
- `学f_ll_cu_s006_v003_d0327_λγ`: orphan_no_importers, unused_exports:1
- `算f_ps_ca_s009_v002_d0327_λS`: orphan_no_importers, unused_exports:1
- `预p_pr_co_s001_v001`: orphan_no_importers, unused_exports:1

## Overcap Files (split candidates)

- `tc_sim` (14095 tok)
- `tc_gemini` (11314 tok)
- `tc_observatory` (11262 tok)
- `u_pj` (10995 tok)
- `tc_popup` (6993 tok)
- `w_gpmo` (6982 tok)
- `w_gpmo` (6980 tok)
- `tc_popup` (6892 tok)

## Active Bug Dossier

**Focus modules:** micro_sim_engine_prompt_file, word_number_file_mapping_for, gemini_api_call_system_prompt, picks_relevant_source_files_based, intent_simulation_on_typing_pause
**Focus bugs:** oc, de

<!-- /pigeon:active-template -->
<!-- pigeon:probe-resolutions -->
## Probe Resolutions

*2 resolved · 2026-04-21 23:15 UTC*

**Read these before editing the referenced modules:**

- **`query_memory`**: operator keeps query_memory as a clot — should it be split, deleted, or repurposed for probe history?
  - → Codebase pattern: 260+ modules, all decomposed by pigeon compiler. Split is the convention. (conf=0.60, via organism_directive)

- **`query_memory`**: operator keeps query_memory as a clot — should it be split, deleted, or repurposed for probe history?
  - → Operator deleted reference to 'delete' — likely intended: The operator was about to specify that the testing should occur after the initial fix has been applied.
---
They likely deleted it because the overall (conf=0.60, via unsaid_recon)

<!-- /pigeon:probe-resolutions -->
