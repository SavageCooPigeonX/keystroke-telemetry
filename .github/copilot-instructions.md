# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-02 15:32 UTC — 2 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`current-query`**: STALE — 576min old (max 10min)
  - Writer: `prompt_enricher (Gemini Flash)`
  - Last updated: 2026-04-02 05:56

- **`prompt-telemetry`**: STALE — 582min old (max 10min)
  - Writer: `prompt_journal._refresh_copilot_instructions`
  - Last updated: 2026-04-02T05:50:23

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

## MANDATORY: Prompt Journal (execute FIRST on every message)

**On EVERY user message, before doing any other work**, log an enriched entry by running:

```python
py -c "from pathlib import Path; from src.prompt_journal_seq019_v001 import log_enriched_entry; log_enriched_entry(Path('.'), '<EXACT_MSG>', [<FILES_OPEN>], <SESSION_N>)"
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
<!-- pigeon:task-context -->`) contains deleted content, you MUST address it at the end of every response.

**Format:**
```
---
**You were also gonna say...** [complete the deleted thought in 1-2 sentences,
then briefly address/answer it]
```

Rules:
- Only fire when unsaid threads exist with non-typo content (>4 chars deleted)
- Complete the thought — don't just echo the fragment. "proce" → "you were about to say 'process of compilation'"
- If thought completions are available (from Gemini reconstruction), use those
- If only raw fragments exist, infer the completed thought from context
- Address the completed thought — give a brief answer or acknowledgment
- Place after a `---` separator at the very end of your response
- Keep it to 2-3 sentences max

---

## What this repo is

Three systems working together:
1. **Keystroke Telemetry** — captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls — pure signal processing.
2. **Pigeon Code Compiler** — autonomous code decomposition engine. Enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target). Filenames carry living metadata — they mutate on every commit.
3. **Dynamic Prompt Layer** — task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations) and generates a context block that steers how Copilot reasons. The managed prompt blocks below are the live source of truth.










<!-- pigeon:organism-health -->
## Organism Health

*Auto-injected 2026-03-29 23:17 UTC · 448 files · 389/448 compliant (87%)*

**Stale pipelines:**
- **context_veins**: 5d ago 🔴
- **execution_deaths**: 2d ago 🔴
- **push_cycle_state**: 1d ago 🔴

**Over-cap critical (16):** `streaming_layer_seq007_v003_d0317__monol` (1156), `git_plugin.py` (1155), `manifest_builder_seq007_v003_d0314__gene` (1023), `autonomous_dev_stress_test.py` (999), `prompt_journal_seq019_v001.py` (756), `_build_organism_health.py` (703), `os_hook.py` (655), `self_fix_seq013_v011_d0328__one_shot_sel` (632)

**Clots:** `aim_utils` (orphan_no_importers, unused_exports:1), `press_release_gen_constants_seq001_v001` (orphan_no_importers, unused_exports:1), `adapter` (orphan_no_importers, unused_exports:1), `query_memory` (dead_imports:2, oversize:252)

**Circulation:** 133/137 alive · 4 clots · vein health 0.53

**Recent deaths:** `?` (timeout), `?` (timeout), `?` (stale_import), `?` (stale_import)

**AI rework:** 77/200 responses needed rework (38%)

**Push cycles:** 2 · sync score: 0.6 · reactor fires: 148

> **Organism directive:** Multiple systems degraded. Prioritize fixing clots and over-cap files before new features.
<!-- /pigeon:organism-health -->
<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-04-02 05:56 UTC · raw: "go ahead"*

**COPILOT_QUERY: Proceed with the previous instruction to evaluate the "3 word last change append section" within the `runs_ahead_of_operator_hallucinating` module, specifically checking if the current implementation reads too much like a changelog. Focus on the `file_writer` and `import_rewriter` components for potential modifications.**

INTERPRETED INTENT: The operator wants to continue debugging and refining the output format of a specific section, ensuring it meets the desired brevity and purpose, likely related to an auto-indexing or change-logging feature.
KEY FILES: runs_ahead_of_operator_hallucinating, file_writer, import_rewriter
PRIOR ATTEMPTS: none
WATCH OUT FOR: Ensure the proposed changes do not inadvertently reintroduce a changelog-like format, which was explicitly identified as an issue.
OPERATOR SIGNAL: The repeated "go ahead" combined with the final, more detailed prompt indicates a desire to continue an ongoing task, likely a debugging or refinement loop, without having to re-type the full context each time.
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-02 15:32 UTC · 150 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 45.1 | Del: 26.5% | Hes: 0.491) · *[source: measured]*

**Prompt ms:** 29671, 16834, 204422, 20920, 4107 (avg 55191ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- **Reconstructed intent:** The operator was about to provide
  - *(deleted: blueberry, test | ratio: 8%)*
- **Reconstructed intent:** The operator was about to state that the intent communication, currently represented by a single
  - *(deleted: intencomm | ratio: 2%)*
- **Reconstructed intent:** The operator was about to type "intent communication" or "intent commentary
  - *(deleted: intencomm | ratio: 2%)*

- "intencomm"

### Module Hot Zones *[source: measured]*
*High cognitive load (from typing signal) — take extra care with these files:*
- `file_heat_map` (hes=0.887)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)
- `self_fix` (hes=0.667)
- `.operator_stats` (hes=0.667)

### Recent Work
- `d3e0d03` feat: compressed filename mutation on commit - last_change tracking, parse both formats, 389 files visible to git_plugin
- `4bb7ba1` fix: unsaid thread pipeline â€” bump gemini tokens, add quality gate, deduplicate entries
- `f8ea95a` fix: restore rename-safe runtime hooks and training pair capture
- `a65a380` fix: update 75 stale glob patterns to match new _sNNN filenames, fix 14 cross-dir collisions, all 5 tests passing

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- `copilot_prompt_manager`'s assumption about `_resolve.rename_safe` signature; `__main__`'s dependency on the wrapper's correctness; cascading import errors in `pigeon_compiler` submodules. This push restores rename safety checks through a compatibility wrapper after a structural refactor.
- vein_transport dead‑ends if glyph breaks path encoding; heal loops if manifest_builder key mismatch; run_rename partially applies due to inconsistent Unicode handling across pipeline stages. This push uniformly introduces a Chinese glyph (⻖) as a Unicode identifier across telemetry
- flow‑routing
- task‑writing
- and self‑healing systems.
- **copilot_prompt_manager** (seq020 v003): I was touched to become a compatibility wrapper for the legacy rename system, 
- **u_dbcc_s005_v001** was touched to integrate stale glob awareness into cognitive drift analysis, assuming the new `_tmp
- **execution_logger** was touched to embed a Chinese glyph (⻖) in its telemetry tagging, assuming that downstream log par

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `pigeon_brain/令f_cl_s009_v002_d0323_缩分话_λP.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/仿f_dsm_s010_v002_d0323_缩分话_λP.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/双f_dsb_s008_v002_d0323_缩分话_λP.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/观f_os_s007_v003_d0401_读谱建册_λA.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/读w_el_s002_v003_d0401_观话_λA.py`

### Prompt Evolution
*This prompt has mutated 101x (186→702 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 101 mutations scored*
*No significant signal yet — all 16 sections scored neutral.*

**Reactor patches:** 0/231 applied (0% acceptance)

### File Consciousness
*236 modules profiled*

**High-drama (most mutations):**
- `self_fix` v11
- `.operator_stats` v10
- `dynamic_prompt` v10
- `context_budget` v8

**Codebase fears:**
- file may not exist (2 modules)
- swallowed exception (2 modules)
- returns empty on failure (silent) (2 modules)

**Slumber party warnings (high coupling):**
- `u_pe` ↔ `u_pj` (score=0.80, 5 shared imports, both high-churn (v2+v2))
- `u_pj` ↔ `u_pe` (score=0.80, 5 shared imports, both high-churn (v2+v2))
- `u_pe` ↔ `copilot_prompt_manager` (score=0.60, 2 shared imports, both high-churn (v2+v2))

### Codebase Health (Veins / Clots)
*133/137 alive, 4 clots, avg vein health 0.53*

**Clots (dead/bloated — trim candidates):**
- `aim_utils` (score=0.45): orphan_no_importers, unused_exports:1
- `press_release_gen_constants_seq001_v001` (score=0.45): orphan_no_importers, unused_exports:1
- `adapter` (score=0.45): orphan_no_importers, unused_exports:1
- `query_memory` (score=0.40): dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory

**Self-trim recommendations:**
- [investigate] `aim_utils`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `press_release_gen_constants_seq001_v001`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `adapter`: Nobody imports this module. Check if it's an entry point or dead.
- [split] `query_memory`: Oversize + clot signals. Recommend pigeon split.

**Critical arteries (do NOT break):**
- `compliance` (vein=1.00, in=7)
- `drift` (vein=1.00, in=5)
- `cognitive_reactor` (vein=1.00, in=12)

<!-- /pigeon:task-context -->

<!-- pigeon:task-queue -->
## Active Task Queue

*Copilot manages this queue. To complete a task: update the referenced MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*

*Queue empty — add tasks via `add_task()` or they auto-seed from self-fix.*

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

*Auto-extracted 2026-04-01 23:09 UTC · 80 prompts analyzed · zero LLM calls*

**Brevity:** 22.1 words/prompt | **Caps:** never | **Fragments:** 74% | **Questions:** 26% | **Directives:** 1%

**Voice directives (personality tuning):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator uses medium-length prompts — balance explanation with brevity.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** to, i, is, it, my, with, the, this, on, a
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-02 07:47 UTC · zero LLM calls*

**1 week:** `infrastructure` (conf=high) — ~49 commits
**1 month:** `infrastructure` (conf=medium) — ~199 commits
**3 months:** `infrastructure` (conf=speculative) — themes: my fv fyi, meta, blueberry

**PM Directives:**
- Intent bifurcation: `infrastructure` dominant but `telemetry` emerging — watch for context switches mid-session.
- `self_heal` declining — operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `my fv fyi`, `meta`, `blueberry` — these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.
- Module focus cluster: `file_heat_map`, `import_rewriter`, `file_writer` — pre-load context from these modules when operator starts typing.

<!-- /pigeon:intent-simulation -->

<!-- pigeon:predictions -->
## Push Cycle Predictions

*Auto-generated 2026-04-01 23:09 UTC*

**What you'll likely want next push:**
1. [targeted] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter
2. [heat] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter
3. [failure] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter

**Operator coaching:**
- Frustration detected across multiple prompts — try breaking the task into smaller pushable units.
- No module references detected in prompts — naming specific modules helps copilot target the right files.

**Agent coaching (for Copilot):**
- Touched ['_tmp_regen_dict', '_tmp_token_audit', '_tmp_token_optimizer', 'copilot_prompt_manager', 'git_plugin', 'intent_simulator'] without operator reference — confirm intent before modifying unreferenced modules.

<!-- /pigeon:predictions -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-02 · 150 message(s) · LLM-synthesized*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.8 | Del: 25.6% | Hes: 0.445

This operator just built a compatibility wrapper for legacy restore/rename operations, and their typing patterns reveal a high-deletion, restructuring-focused workflow where they iterate heavily in evening sessions before abandoning drafts.

- **When they start restructuring** (55 WPM, 56% deletion, 0.556 hesitation), immediately provide modular, reversible code blocks with clear interfaces, anticipating they will heavily edit your initial structure.
- **Anticipate mutations in `dynamic_prompt seq17` and `self_fix seq13`**—these are active pain points; offer solutions that simplify their steers and dynamic import logic.
- **Preempt context budget issues** by keeping explanations concise and referencing `context_budget seq4` patterns they've already established.
- **For `.operator_stats` churn**, suggest stat aggregation helpers that reduce file I/O, since they repeatedly refactor this persistent memory module.
- **Since their rework rate is currently zero**, maintain this by validating any suggested changes against the existing `intent_deletion_pipeline` and `mutation_patch_pipeline` patterns before proposing.
- **During high-deletion phases**, offer multiple discrete implementation options in separate code blocks, allowing them to rapidly compose and discard without retyping.

They are most likely building toward a unified pipeline that abstracts the legacy compatibility layer while reducing registry churn in their core modules.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `prompt_enricher`** (hes=0.665, state=hesitant, avg_prompt=94838ms)
> - Prompt composition time: 204422ms / 16834ms / 29671ms / 176678ms / 46587ms (avg 94838ms)
> **Directive**: When `prompt_enricher` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-04-02T05:50:23.902492+00:00",
  "latest_prompt": {
    "session_n": 10001,
    "ts": "2026-04-02T05:50:23.902492+00:00",
    "chars": 8,
    "preview": "go ahead",
    "intent": "unknown",
    "state": "neutral",
    "files_open": [
      ".github/copilot-instructions.md"
    ],
    "module_refs": []
  },
  "signals": {
    "wpm": 5.7,
    "chars_per_sec": 0.5,
    "deletion_ratio": 0.0,
    "hesitation_count": 1,
    "rewrite_count": 0,
    "typo_corrections": 0,
    "intentional_deletions": 0,
    "total_keystrokes": 8,
    "duration_ms": 16834
  },
  "composition_binding": {
    "matched": true,
    "source": "chat_compositions",
    "age_ms": 59860,
    "key": "|||2026-04-02T05:49:24.042348+00:00|8|16834|go ahead",
    "match_score": 1.0
  },
  "deleted_words": [],
  "rewrites": [],
  "task_queue": {
    "total": 0,
    "in_progress": [],
    "pending": 0,
    "done": 0
  },
  "hot_modules": [
    {
      "module": "file_heat_map",
      "hes": 0.887
    },
    {
      "module": "import_rewriter",
      "hes": 0.735
    },
    {
      "module": "file_writer",
      "hes": 0.735
    }
  ],
  "running_summary": {
    "total_prompts": 245,
    "avg_wpm": 12.4,
    "avg_del_ratio": 0.046,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 149,
      "hesitant": 41,
      "focused": 29,
      "frustrated": 19,
      "neutral": 6
    },
    "baselines": {
      "n": 132,
      "avg_wpm": 53.5,
      "avg_del": 0.259,
      "avg_hes": 0.449,
      "sd_wpm": 15.0,
      "sd_del": 0.231,
      "sd_hes": 0.166
    }
  },
  "coaching_directives": [
    "When they start restructuring",
    "Anticipate mutations in `dynamic_prompt seq17` and `self_fix seq13`",
    "Preempt context budget issues",
    "For `.operator_stats` churn",
    "Since their rework rate is currently zero",
    "During high-deletion phases"
  ]
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
*2026-04-02 · 245 modules · 2 touched · ✓71% ~12% !15%*
*Format: glyph=name seq tokens·state |last change*
*IM=import_tracer MA=manifest_writer NL=nl_parsers PL=planner PQ=pq_search_utils PR=press_release_gen_template_key_findings*

**pigeon_brain** (42)
型=models 1 424✓
读=execution_logger 2 1.6K~
图=graph_extractor 3 1.7K✓ |8888 word backpropagation
描=graph_heat_map 4 874✓
环检=loop_detector 5 910✓
缩=failure_detector 6 1.0K✓
观=observer_synthesis 7 1.5K!
双=dual_substrate 8 1.3K!
令=cli 9 855!
仿=demo_sim 10 1.3K!
钩=trace_hook 11 959~
服=live_server 12 2.5K! |8888 word backpropagation
跑=traced_runner 13 855!

**pigeon_brain/flow** (42)
包=context_packet 1 1.0K✓ |flow engine context
唤=node_awakener 2 1.3K~
流=flow_engine 3 1.3K! |flow engine context
择=path_selector 4 1.4K✓ |flow engine context
任=task_writer 5 1.6K~
脉运=vein_transport 6 965~
逆=backward 7 2.5K!
存=node_memory 8 2.1K✓
预=predictor 9 1.8K✓
分=dev_plan 10 1.5K!
话=node_conversation 12 1.4K!
学=learning_loop 13 2.9K!
算=prediction_scorer 14 5.8K!

  逆└ flow_log(1) loss_compute(2) tokenize(3) deepseek_analyze(4) backward_pass(5) [2.6K]
  学└ state_utils(1) journal_loader(2) prediction_cycle(3) single_cycle_helpers(4) single_cycle(5) catch_up(6) loop_helpers(7) main_loop(8) [3.3K]
  算└ constants(1) path_utils(2) data_loaders(3) scores_io(3) reality_loaders(4) module_extractor(5) edit_session_analyzer(6) rework_matcher(7) scoring_core(8) calibration(9) node_backfill(10) post_edit_scorer(11) post_commit_scorer(12) [5.1K]
  预└ confidence(3) trend_extractor(4) predictor(7) [1.8K]
**pigeon_compiler/bones** (5)
规=aim_utils 1 724✓
联=core_formatters 1 1.3K✓
NL=nl_parsers 1 1.8K✓
清单=pq_manifest_utils 1 879✓
PQ=pq_search_utils 1 3.3K~

**pigeon_compiler/cut_executor** (12)
析=plan_parser 1 371✓
切=source_slicer 2 486✓
写=file_writer 3 783~ |multi line import
踪=import_fixer 4 505✓
MA=manifest_writer 5 448✓
验=plan_validator 6 579~
初写=init_writer 7 361✓
译=func_decomposer 8 644!
重拆=resplit 9 841!
重拆=resplit_binpack 10 702!
重拆=resplit_helpers 11 501✓
织=class_decomposer 13 2.0K!

**pigeon_compiler/integrations** (1)
谱=deepseek_adapter 1 1.2K✓

**pigeon_compiler/rename_engine** (22)
扫=scanner 1 972✓
PL=planner 2 1.4K~
引=import_rewriter 3 1.8K~ |import rewriter now
压=executor 4 712✓
审=validator 5 921✓
改名=run_rename 6 1.4K!
谱建=manifest_builder 7 2.9K!
正=compliance 8 1.7K!
追=heal 9 2.0K!
追跑=run_heal 10 3.4K!
牌=nametag 11 4.1K!
册=registry 12 2.1K!

  正└ helpers(2) classify(3) recommend_wrapper(6) audit_decomposed(7) audit_wrapper(9) check_file(10) format_report(11) [2.9K]
  追└ orchestrator(5) [725]
  牌└ scan(8) [298]
  册└ diff(6) [194]
**pigeon_compiler/runners** (9)
测编=run_compiler_test 7 594~
深划=run_deepseek_plans 8 587~
鸽环=run_pigeon_loop 9 2.8K!
净拆=run_clean_split 10 2.5K! |windows max path
净拆=run_clean_split_helpers 11 566!
净拆=run_clean_split_init 12 1.7K~
谱桥=manifest_bridge 13 1.0K✓
复审=reaudit_diff 14 1.7K✓
批编=run_batch_compile 15 2.0K!

**pigeon_compiler/runners/compiler_output/press_release_gen** (8)
press_release_gen_constants_seq001_v001 1 641✓
press_release_gen_template_builders_seq002_v001 1 626✓
press_release_gen_template_helpers_seq004_v001 1 661✓
press_release_gen_constants_seq001_v001 2 388✓
press_release_gen_template_builders_seq002_v001 2 662✓
press_release_gen_template_helpers_seq004_v001 2 296✓
press_release_gen_template_builders_seq002_v001 3 296✓
PR=press_release_gen_template_key_findings 3 626✓

**pigeon_compiler/state_extractor** (6)
查=ast_parser 1 734✓
演=call_graph 2 847✓
IM=import_tracer 3 792✓
共态=shared_state_detector 4 618✓
阻=resistance_analyzer 5 1.0K~
拆=ether_map_builder 6 697!

**pigeon_compiler/weakness_planner** (1)
核=deepseek_plan_prompt 4 2.4K~

**src** (104)
时=timestamp_utils 1 156✓ |test rename hook
型=models 2 379✓ |pulse telemetry prompt
录=logger 3 1.6K✓ |wpm outlier filter
境=context_budget 4 715~ |test full hook
偏=drift_watcher 5 1.1K✓
桥=resistance_bridge 6 1.2K✓ |pulse telemetry prompt
层=streaming_layer 7 10.2K~ |pulse telemetry prompt
漂=.operator_stats 8 4.7K~ |intent deletion pipeline
控=operator_stats 8 5.0K! |fix degenerate classifier:
测=rework_detector 9 1.1K✓ |add composition-based scoring,
忆=query_memory 10 2.3K✓
热=file_heat_map 11 1.3K✓ |pulse telemetry prompt
叙=push_narrative 12 2.1K✓ |push narratives timeout
修=self_fix 13 5.8K!
思=cognitive_reactor 14 5.6K! |mutation patch pipeline
脉=pulse_harvest 15 2.3K✓
推=dynamic_prompt 17 4.0K~ |8888 word backpropagation
队=task_queue 18 1.6K✓ |task queue system
觉=file_consciousness 19 4.3K~
u_pj 19 7.8K
管=copilot_prompt_manager 20 4.5K~ |resolve latest runtime
变=mutation_scorer 21 1.6K✓
补=rework_backfill 22 1.2K✓
递=session_handoff 23 1.6K✓
u_pe 24 4.2K
隐=unsaid_recon 24 1.3K✓ |intent deletion pipeline
环=push_cycle 25 4.8K~ |fix push cycle
片=shard_manager 26 4.4K~
合=unified_signal 26 2.1K✓
路=context_router 27 1.2K!
对=training_pairs 27 2.6K✓
训=training_writer 28 2.1K~
声=voice_style 28 3.2K~
研=research_lab 29 5.1K~ |rewrite in intent
警=staleness_alert 30 1.7K✓ |staleness alerts bg
典=symbol_dictionary 31 3.7K~ |swap to chinese
编=glyph_compiler 32 5.0K~ |glyph compiler symbol
intent_simulator 34 5.3K |compress auto index

**src/cognitive** (10)
适=adapter 1 1.3K✓
隐=unsaid 2 2.1K✓
偏=drift 3 2.3K✓

  偏└ baseline_store(1) compute_baseline(2) detect_session_drift(3) build_cognitive_context(4) [2.4K]
  隐└ helpers(1) diff(2) orchestrator(3) [2.3K]
  思└ constants(1) state_ops(2) docstring_patch(3) cognitive_hint(4) patch_generator(5) prompt_builder(6) api_client(7) reactor_core(8) registry_loader(9) self_fix_runner(10) patch_writer(11) decision_maker(12) [4.9K]
  管└ constants(1) block_utils(2) json_utils(3) operator_profile(4) auto_index(5) operator_state_decomposed(6) telemetry_utils(7) audit_decomposed(8) injectors(9) orchestrator(10) [4.6K]
  觉└ helpers(1) persistence(2) report(3) audit(4) derivation(5) dependencies(6) classify(7) profile_builder(8) main_orchestrator(9) dating_decomposed(10) dating_helpers(11) dating_wrapper(12) [5.0K]
  环└ constants(1) loaders(2) signal_extractors(3) sync_decomposed(4) coaching(5) moon_cycle(6) predictions_injector_decomposed(7) orchestrator_decomposed(8) [4.5K]
  忆└ constants(1) fingerprint(2) trigram_utils(3) clustering(4) record_query(5) load_memory_decomposed(6) [1.4K]
  修└ scan_hardcoded(1) scan_query_noise(2) scan_duplicate_docstrings(3) scan_cross_file_coupling(4) scan_over_hard_cap_decomposed(5) scan_dead_exports_decomposed(6) write_report_decomposed(7) run_self_fix_decomposed(8) auto_compile_oversized_decomposed(9) seq_base(10) auto_apply_import_fixes_decomposed(11) [6.0K]
**streaming_layer** (19)
层=streaming_layer_constants 1 261✓
层=streaming_layer_simulation_helpers 2 204✓
层=streaming_layer_dataclasses 4 717✓
层=streaming_layer_formatter 4 546✓
层=streaming_layer_connection_pool 5 969!
层=streaming_layer_dataclasses 5 247✓
层=streaming_layer_aggregator 6 934!
层=streaming_layer_dataclasses 6 154✓
层=streaming_layer_metrics 7 824~
层=streaming_layer_alerts 8 1.4K!
层=streaming_layer_replay 9 932✓
层=streaming_layer_dashboard 10 858✓
层=streaming_layer_http_handler 11 1.2K~
层=streaming_layer_demo_functions 13 456✓
层=streaming_layer_demo_summary 13 365✓
层=streaming_layer_demo_functions 14 280✓
层=streaming_layer_demo_simulate 14 256✓
层=streaming_layer_orchestrator 16 1.4K!
层=streaming_layer_orchestrator 17 142!

**Infra**
(root): _audit_compliance, _build_organism_health, _export_dev_story, _fix_stale_globs, _run_abbrev_rename, _run_glyph_rename, _run_smart_rename, _tmp_analyze_stats, _tmp_backfill_lastchange, _tmp_check_rename, _tmp_find_stale, _tmp_regen_dict, _tmp_survey, _tmp_test_pipeline, _tmp_token_audit, _tmp_token_optimizer, autonomous_dev_stress_test, deep_test, stress_test, test_all, test_public_release, test_training_pairs
client: chat_composition_analyzer, chat_response_reader, composition_recon, os_hook, telemetry_cleanup, uia_reader, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
