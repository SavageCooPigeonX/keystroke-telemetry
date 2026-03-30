# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

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

*Enriched 2026-03-30 06:28 UTC · raw: "categorize training pairs per shard for better context routing"*

**COPILOT_QUERY: Implement a mechanism to categorize `training_pairs` within each `shard` to optimize `context_routing` for the LLM. Specifically, modify `pulse_harvest_pairs_prompts_to` to include shard-based categorization logic for training data, and update `context_budget_scorer_for_llm` to leverage this categorization for more effective context selection.**

INTERPRETED INTENT: The operator wants to improve the relevance and efficiency of context provided to the LLM by organizing training data more granularly at the shard level.
KEY FILES: pulse_harvest_pairs_prompts_to, context_budget_scorer_for_llm, context_budget
PRIOR ATTEMPTS: none
WATCH OUT FOR: Ensure the categorization logic is robust and doesn't introduce new performance bottlenecks, especially given the operator's recent focus on speed (GeminiFlash).
OPERATOR SIGNAL: The operator is exploring ways to improve context relevance and efficiency, specifically by organizing training data, and is concerned about the prompt enricher's performance and its impact on context.
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-03-30 06:33 UTC · 6253 messages profiled · 8 recent commits*

**Current focus:** building new features
**Cognitive state:** `hesitant` (WPM: 632.9 | Del: 39.3% | Hes: 0.573) · *[source: measured]*

**Prompt ms:** 4407, 59530, 10748, 102401, 41809 (avg 43779ms)

> **CoT directive:** Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- **Reconstructed intent:** Find the hidden word "
  - *(deleted: : donut | ratio: 35%)*
- **Reconstructed intent:** Refactor the entire
  - *(deleted: can you also refactor the, entire learning loop | ratio: 55%)*

- "is hidden"
- "post write"
- "log to"
- "pirs sho"
- "r - training"

### Module Hot Zones *[source: measured]*
*High cognitive load (from typing signal) — take extra care with these files:*
- `file_heat_map` (hes=0.887)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)
- `init_writer` (hes=0.63)
- `context_budget` (hes=0.587)

### Recent Work
- `1f4291d` feat: organism health system + README rewrite + 4 compiled packages + root cleanup
- `fd2ab12` feat: selection-aware OS hook + moon cycle prediction wiring + gemini unsaid recon
- `b1971c0` fix: dynamic import resolvers + rewrite auto_apply_import_fixes
- `804937e` feat: adaptive WPM baselines (decay-weighted window 200) + signal/narrative split + push cycle + DTR S01E03

### Coaching Directives *[source: llm_derived]*
*LLM-synthesized behavioral rules — treat as hypothesis, not measurement:*
- **Anticipate structural changes**
- **When they edit high-churn modules**
- **Their high deletion rate (46.7%) signals heavy rewriting**
- **Leverage their night-time flow states**

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- os_hook returning null for valid editors
- massive selection data truncating prompts
- and IPC serialization failure in the extension bridge. This push wires real-time editor selection and context into the Copilot steering and push narration loop.
- **git_plugin** was touched to align commit messages with the new selection-aware narratives; I assume the push cycle pas
- **file_consciousness_seq019_helpers** was touched to provide core utilities for health state derivation; it assumes inpu
- **file_consciousness_seq019_persistence** was touched to store health reports; it assumes the database connection pool i
- **push_cycle_seq025_constants** was touched to add health-related thresholds; it assumes these constants are imported be
- **backward_seq007_backward_pass** was touched to integrate dynamic import resolvers for electron path traversal, assumin

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_brain/flow/node_memory_seq008_v003_d0328__the_experience_vault_stores_raw_lc_dynamic_import_resolvers.py`
- [HIGH] over_hard_cap in `pigeon_brain/live_server_seq012_v003_d0324__websocket_server_for_live_execution_lc_8888_word_backpropagation.py`
- [HIGH] over_hard_cap in `pigeon_brain/live_server_seq012_v004_d0324__websocket_server_for_live_execution_lc_8888_word_backpropagation.py`
- [HIGH] over_hard_cap in `pigeon_brain/live_server_seq012_v004_d0324__websocket_server_for_live_execution_lc_per_prompt_deleted.py`
- [HIGH] over_hard_cap in `pigeon_compiler/runners/run_batch_compile_seq015_v002_d0328__compile_entire_codebase_to_pigeon_lc_dynamic_import_resolvers.py`

### Prompt Evolution
*This prompt has mutated 71x (186→843 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### File Consciousness
*217 modules profiled*

**High-drama (most mutations):**
- `self_fix` v11 ↔ .operator_stats
- `.operator_stats` v9 ↔ operator_stats
- `context_budget` v8 ↔ streaming_layer
- `dynamic_prompt` v8 ↔ run_pigeon_loop

**Codebase fears:**
- file may not exist (75 modules)
- returns empty on failure (silent) (44 modules)
- swallowed exception (38 modules)

**Slumber party warnings (high coupling):**
- `cli` ↔ `trace_hook` (score=0.80, 3 shared imports, both high-churn (v2+v2))
- `cli` ↔ `traced_runner` (score=0.80, 3 shared imports, both high-churn (v2+v2))
- `demo_sim` ↔ `execution_logger` (score=0.80, 3 shared imports, both high-churn (v2+v2))

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

*Auto-extracted 2026-03-30 00:49 UTC · 60 prompts analyzed · zero LLM calls*

**Brevity:** 22.6 words/prompt | **Caps:** never | **Fragments:** 82% | **Questions:** 15% | **Directives:** 13%

**Voice directives (personality tuning):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator uses medium-length prompts — balance explanation with brevity.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** to, this, you, is, in, test, and, the, a, prompt
<!-- /pigeon:voice-style -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-03-30 · 6253 message(s) · LLM-synthesized*

**Dominant: `frustrated`** | Submit: 3% | WPM: 53.4 | Del: 46.6% | Hes: 0.648

The operator just built an organism health system by batch-renaming 35 modules with automated compiler tags, revealing a high-velocity, night-focused pattern of systematic refactoring with significant deletions, indicating they are aggressively consolidating and versioning a complex system.

*   **Anticipate structural changes** in `self_fix_seq013` and `dynamic_prompt_seq017`; they are recurring pain points, so prioritize understanding their new interfaces and dependencies when providing code.
*   **When they edit high-churn modules**, offer completions that reflect the new `_v002_d0329__auto_extracted_by_pigeon_compiler` naming convention and suggest imports that match this versioned structure.
*   **Their high deletion rate (46.7%) signals heavy rewriting**; after large edits, proactively summarize the changed function signatures or class structures to confirm alignment.
*   **Leverage their night-time flow states**; when they exhibit high WPM with low hesitation, provide concise, direct code blocks without explanatory prose.

Given the zero miss rate, maintain the current response quality but **preempt import and reference errors** in the freshly renamed modules by cross-checking the new filenames against calls in `push_cycle_seq025` and `operator_stats_seq8`.

They are most likely building toward an integrated, version-aware compilation pipeline that automates module extraction and dependency resolution.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `node_conversation`** (hes=0.698, state=hesitant, avg_prompt=33623ms)
> - Prompt composition time: 9438ms / 41929ms / 6437ms / 98174ms / 12136ms (avg 33623ms)
> **Directive**: When `node_conversation` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-03-30T02:31:44.064135+00:00",
  "latest_prompt": {
    "session_n": 5,
    "ts": "2026-03-30T02:31:44.064135+00:00",
    "chars": 188,
    "preview": "are you guessing or estimating 0 i assume this is only valueble for compiler 0 hows prediction engine working and how many llm lcalls are used - what info can you find that im not aware of",
    "intent": "exploring",
    "state": "focused",
    "files_open": [
      ".github/copilot-instructions.md"
    ],
    "module_refs": []
  },
  "signals": {
    "wpm": 52.4,
    "chars_per_sec": 4.4,
    "deletion_ratio": 0.005,
    "hesitation_count": 1,
    "rewrite_count": 0,
    "typo_corrections": 0,
    "intentional_deletions": 1,
    "total_keystrokes": 191,
    "duration_ms": 43526
  },
  "composition_binding": {
    "matched": true,
    "source": "chat_compositions",
    "age_ms": 63700,
    "key": "|||2026-03-30T02:30:40.364508+00:00|191|43526|are you guessing or estimating 0 i assume this is only valueble for compiler 0 hows prediction engine working and how ma",
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
    "total_prompts": 70,
    "avg_wpm": 26.2,
    "avg_del_ratio": 0.033,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 57,
      "focused": 6,
      "hesitant": 5,
      "neutral": 1,
      "frustrated": 1
    },
    "baselines": {
      "n": 101,
      "avg_wpm": 115.5,
      "avg_del": 0.486,
      "avg_hes": 0.681,
      "sd_wpm": 35.8,
      "sd_del": 0.073,
      "sd_hes": 0.069
    }
  }
}
```

<!-- /pigeon:prompt-telemetry -->
---

## Module Map

### src/ — Core Telemetry
| Module (search by) | Role | Key exports |
|---|---|---|
| `timestamp_utils_seq001*` | epoch ms utility | `_now_ms` |
| `models_seq002*` | dataclasses | `KeyEvent`, `MessageDraft` |
| `logger_seq003*` | core logger | `TelemetryLogger`, `SCHEMA_VERSION` |
| `context_budget_seq004*` | token cost scorer | `score_context_budget`, `estimate_tokens` |
| `drift_watcher_seq005*` | file-size drift | `DriftWatcher` |
| `resistance_bridge_seq006*` | telemetry→compiler bridge | `HesitationAnalyzer` |
| `streaming_layer_seq007*` | **MONOLITH 1150 lines** (test harness only) | 8 classes |
| `operator_stats_seq008*` | persistent profile writer | `OperatorStats` |
| `rework_detector_seq009*` | AI answer quality measurement | `score_rework`, `record_rework` |
| `query_memory_seq010*` | recurring query + unsaid detector | `QueryMemory` |
| `file_heat_map_seq011*` | cognitive load per module | `FileHeatMap` |
| `push_narrative_seq012*` | per-push narrative generation | `generate_push_narrative` |
| `self_fix_seq013*` | one-shot self-fix analyzer | `analyze_and_fix` |
| `cognitive_reactor_seq014*` | autonomous code modification | `CognitiveReactor` |
| `pulse_harvest_seq015*` | prompt→file edit pairing | `harvest_pulse` |
| `prompt_recon_seq016*` | prompt reconstruction + mutation tracking | `reconstruct_all`, `track_copilot_prompt_mutations` |
| `dynamic_prompt_seq017*` | **task-aware CoT injection** | `build_task_context`, `inject_task_context` |

### src/cognitive/ — Intelligence Layer
| Module | Role |
|---|---|
| `adapter_seq001*` | state → prompt modifier |
| `unsaid_seq002*` | **monolith** (compiled package: `src/cognitive/unsaid/`) |
| `drift_seq003*` | **monolith** (compiled package: `src/cognitive/drift/`) |

**Note**: `src/cognitive/unsaid/` and `src/cognitive/drift/` are compiled packages (pigeon-compliant). The `unsaid_seq002*` and `drift_seq003*` monolith files in `src/cognitive/` are legacy artifacts — prefer importing from the packages.

### src/operator_stats/ — Compiled Package (14 files)
Source was `src/operator_stats_seq008*` (394 lines). Compiled to `src/operator_stats/` package. Both exist currently.

### streaming_layer/ — 19 files, 100% compliant
Compiled streaming interface. `streaming_layer_orchestrator_seq016/017` are the entry points.

### pigeon_compiler/ — The Compiler (~62 modules)
| Subpackage | Role |
|---|---|
| `state_extractor/` | AST parsing, call graphs, resistance scoring |
| `weakness_planner/` | DeepSeek cut plan generation |
| `cut_executor/` | file slicing, bin-packing, class decomposition |
| `rename_engine/` | autonomous renames, import rewriting, self-healing |
| `runners/` | pipeline orchestrators |
| `integrations/` | DeepSeek API adapter |
| `bones/` | shared utilities |

**Key compiler entry points**:
- `py -m pigeon_compiler.runners.run_clean_split_seq010*` — compile one file
- `py -m pigeon_compiler.runners.run_batch_compile_seq015*` — compile entire codebase
- `py -m pigeon_compiler.runners.run_heap_seq010*` — self-heal pipeline
- `py -m pigeon_compiler.git_plugin` — post-commit hook

---

## Registry & State Files

| File | Purpose |
|---|---|
| `pigeon_registry.json` | tracks every module: seq, ver, date, desc, intent, token history |
| `operator_profile.md` | living operator cognitive profile (auto-updated every 8 messages) |
| `MASTER_MANIFEST.md` | auto-generated project map (rebuilt on every commit) |
| `**/MANIFEST.md` | per-folder manifest, auto-rebuilt |
| `logs/pigeon_sessions/{name}.jsonl` | mutation audit trail per module |
| `test_logs/`, `demo_logs/`, `stress_logs/` | telemetry session data |

---

## Tests

```bash
py test_all.py   # 4 tests, all must pass, zero deps beyond stdlib
```

| Test | Covers |
|---|---|
| TEST 1 | TelemetryLogger — v2 schema, 3 turns, submit + discard |
| TEST 2 | Context Budget Scorer — hard cap, budget, coupling |
| TEST 3 | DriftWatcher — baseline + versioned filename drift |
| TEST 4 | Resistance Bridge — telemetry → compiler signal |

**Always run tests after edits.** If a test imports a file by full name, it will break after a pigeon rename — use glob/search patterns in tests.

---

## Common Pitfalls

- **Never hardcode full pigeon filenames** — they mutate on every commit. Use `file_search("module_name_seq*")`.
- **`py` not `python`** — this is Windows, use `py` launcher.
- **UTF-8 encoding** — always `$env:PYTHONIOENCODING = "utf-8"` in PowerShell terminal.
- **Imports follow the pigeon name** — when a file is renamed, all `import` / `from` statements across the codebase are auto-rewritten by `rewrite_all_imports()`.
- **Don't delete monolith originals yet** — `src/operator_stats_seq008*`, `src/cognitive/unsaid_seq002*`, `src/cognitive/drift_seq003*` are still imported in some places. Verify before removing.
- **`streaming_layer_seq007*` is intentionally left as a 1150-line test harness** — drift_watcher tests flag it as OVER_HARD_CAP on purpose.
- **DeepSeek timeout** — phase 2 LLM calls can timeout; retry with a fresh call, don't loop.

---

### Full Module Index
<!-- pigeon:auto-index -->
*Auto-updated 2026-03-29 - 248 modules tracked | 37 touched this commit*

**pigeon_brain/** - 16 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `models_seq001*` | isomorphic to keystroke models | ~424 |
| `execution_logger_seq002*` | isomorphic to telemetrylogger for agent | ~1,541 |
| `graph_extractor_seq003*` | extract the cognition graph from | ~1,744 |
| `graph_extractor_seq003*` | extract the cognition graph from | ~1,744 |
| `graph_heat_map_seq004*` | failure accumulator per node port | ~874 |
| `loop_detector_seq005*` | recurring path detection port of | ~910 |
| `failure_detector_seq006*` | electron death classification port of | ~1,018 |
| `observer_synthesis_seq007*` | coaching from execution patterns port | ~1,357 |
| `dual_substrate_seq008*` | merges human and agent telemetry | ~1,314 |
| `cli_seq009*` | build graph run observer export | ~855 |
| `demo_sim_seq010*` | generates execution telemetry from the | ~1,276 |
| `trace_hook_seq011*` | instruments python calls between pigeon | ~959 |
| `live_server_seq012*` | websocket server for live execution | ~2,495 |
| `live_server_seq012*` | websocket server for live execution | ~2,857 |
| `live_server_seq012*` | websocket server for live execution | ~2,857 |
| `traced_runner_seq013*` | run any python script with | ~855 |

**pigeon_brain/flow/** - 18 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `context_packet_seq001*` | the contextpacket is the unit | ~1,033 |
| `node_awakener_seq002*` | when a packet arrives at | ~1,171 |
| `flow_engine_seq003*` | the flow engine is the | ~1,316 |
| `path_selector_seq004*` | path selection is the real | ~1,373 |
| `task_writer_seq005*` | the river delta where all | ~1,476 |
| `vein_transport_seq006*` | as a packet flows along | ~884 |
| `backward_seq007*` | backward pass walks electron path | ~2,502 |
| `backward_seq007*` | backward pass walks electron path | ~2,500 |
| `node_memory_seq008*` | the experience vault stores raw | ~2,084 |
| `predictor_seq009*` | fires phantom electrons using cognitive | ~1,762 |
| `predictor_seq009*` | fires phantom electrons using cognitive | ~1,831 |
| `dev_plan_seq010*` | the roadmap writer synthesizes the | ~1,532 |
| `dev_plan_seq010*` | the roadmap writer synthesizes the | ~1,539 |
| `dev_plan_seq010*` | the roadmap writer synthesizes the | ~1,541 |
| `node_conversation_seq012*` | the interpretability interface lets the | ~1,422 |
| `node_conversation_seq012*` | the interpretability interface lets the | ~1,428 |
| `learning_loop_seq013*` | the perpetual learning loop | ~2,881 |
| `prediction_scorer_seq014*` | edit session based | ~4,294 |

**pigeon_brain/flow/backward_seq007/** - 7 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `backward_seq007_flow_log_seq001*` | auto extracted by pigeon compiler | ~423 |
| `backward_seq007_loss_compute_seq002*` | auto extracted by pigeon compiler | ~187 |
| `backward_seq007_tokenize_seq003*` | auto extracted by pigeon compiler | ~307 |
| `backward_seq007_deepseek_analyze_seq004*` | auto extracted by pigeon compiler | ~772 |
| `backward_seq007_deepseek_analyze_seq004*` | auto extracted by pigeon compiler | ~774 |
| `backward_seq007_backward_pass_seq005*` | auto extracted by pigeon compiler | ~908 |
| `backward_seq007_backward_pass_seq005*` | auto extracted by pigeon compiler | ~910 |

**pigeon_brain/flow/learning_loop_seq013/** - 14 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `learning_loop_seq013_state_utils_seq001*` | auto extracted by pigeon compiler | ~284 |
| `learning_loop_seq013_journal_loader_seq002*` | auto extracted by pigeon compiler | ~192 |
| `learning_loop_seq013_prediction_cycle_seq003*` | auto extracted by pigeon compiler | ~415 |
| `learning_loop_seq013_prediction_cycle_seq003*` | auto extracted by pigeon compiler | ~431 |
| `learning_loop_seq013_prediction_cycle_seq003*` | auto extracted by pigeon compiler | ~431 |
| `learning_loop_seq013_single_cycle_helpers_seq004*` | auto extracted by pigeon compiler | ~25 |
| `learning_loop_seq013_single_cycle_seq005*` | auto extracted by pigeon compiler | ~880 |
| `learning_loop_seq013_single_cycle_seq005*` | auto extracted by pigeon compiler | ~896 |
| `learning_loop_seq013_single_cycle_seq005*` | auto extracted by pigeon compiler | ~896 |
| `learning_loop_seq013_catch_up_seq006*` | auto extracted by pigeon compiler | ~431 |
| `learning_loop_seq013_catch_up_seq006*` | auto extracted by pigeon compiler | ~431 |
| `learning_loop_seq013_loop_helpers_seq007*` | auto extracted by pigeon compiler | ~23 |
| `learning_loop_seq013_main_loop_seq008*` | auto extracted by pigeon compiler | ~1,044 |
| `learning_loop_seq013_main_loop_seq008*` | auto extracted by pigeon compiler | ~1,044 |

**pigeon_brain/flow/prediction_scorer_seq014/** - 16 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `prediction_scorer_seq014_constants_seq001*` | auto extracted by pigeon compiler | ~73 |
| `prediction_scorer_seq014_path_utils_seq002*` | auto extracted by pigeon compiler | ~79 |
| `prediction_scorer_seq014_data_loaders_seq003*` | auto extracted by pigeon compiler | ~514 |
| `prediction_scorer_seq014_scores_io_seq003*` | auto extracted by pigeon compiler | ~181 |
| `prediction_scorer_seq014_reality_loaders_seq004*` | auto extracted by pigeon compiler | ~374 |
| `prediction_scorer_seq014_module_extractor_seq005*` | auto extracted by pigeon compiler | ~112 |
| `prediction_scorer_seq014_edit_session_analyzer_seq006*` | auto extracted by pigeon compiler | ~187 |
| `prediction_scorer_seq014_rework_matcher_seq007*` | auto extracted by pigeon compiler | ~460 |
| `prediction_scorer_seq014_scoring_core_seq008*` | auto extracted by pigeon compiler | ~713 |
| `prediction_scorer_seq014_calibration_seq009*` | auto extracted by pigeon compiler | ~419 |
| `prediction_scorer_seq014_node_backfill_seq010*` | auto extracted by pigeon compiler | ~496 |
| `prediction_scorer_seq014_node_backfill_seq010*` | auto extracted by pigeon compiler | ~499 |
| `prediction_scorer_seq014_post_edit_scorer_seq011*` | auto extracted by pigeon compiler | ~839 |
| `prediction_scorer_seq014_post_edit_scorer_seq011*` | auto extracted by pigeon compiler | ~841 |
| `prediction_scorer_seq014_post_commit_scorer_seq012*` | auto extracted by pigeon compiler | ~605 |
| `prediction_scorer_seq014_post_commit_scorer_seq012*` | auto extracted by pigeon compiler | ~607 |

**pigeon_compiler/bones/** - 5 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `aim_utils_seq001*` | extracted from hush aim py | ~724 |
| `core_formatters_seq001*` | extracted from hush chat core | ~1,291 |
| `nl_parsers_seq001*` | extracted from hush nl detection | ~1,844 |
| `pq_manifest_utils_seq001*` | extracted from hush pre query | ~879 |
| `pq_search_utils_seq001*` | extracted from hush pre query | ~3,279 |

**pigeon_compiler/cut_executor/** - 12 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `plan_parser_seq001*` | parse deepseek json from raw | ~371 |
| `source_slicer_seq002*` | extract functions constants from source | ~486 |
| `file_writer_seq003*` | write new pigeon compliant files | ~783 |
| `import_fixer_seq004*` | update imports across the project | ~505 |
| `manifest_writer_seq005*` | generate manifest md for a | ~448 |
| `plan_validator_seq006*` | validate cut plan before execution | ~579 |
| `init_writer_seq007*` | generate init py for split | ~361 |
| `func_decomposer_seq008*` | decompose oversized functions via deepseek | ~644 |
| `resplit_seq009*` | deterministic ast bin packing re | ~841 |
| `resplit_binpack_seq010*` | bin packing file writing for | ~702 |
| `resplit_helpers_seq011*` | shared helpers for re splitter | ~501 |
| `class_decomposer_seq013*` | decompose oversized classes via deepseek | ~1,959 |

**pigeon_compiler/integrations/** - 1 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `deepseek_adapter_seq001*` | deepseek api client | ~1,180 |

**pigeon_compiler/rename_engine/** - 12 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `scanner_seq001*` | walk the project tree and | ~972 |
| `planner_seq002*` | generate rename plan for non | ~919 |
| `import_rewriter_seq003*` | rewrite all imports across the | ~1,750 |
| `executor_seq004*` | execute file renames with rollback | ~712 |
| `validator_seq005*` | post rename import validation | ~921 |
| `run_rename_seq006*` | full rename pipeline runner | ~1,374 |
| `manifest_builder_seq007*` | generate living manifest md per | ~2,927 |
| `compliance_seq008*` | line count enforcer split recommender | ~1,673 |
| `heal_seq009*` | self healing orchestrator | ~2,044 |
| `run_heal_seq010*` | automated self healing pipeline | ~3,431 |
| `nametag_seq011*` | encode file description intent into | ~1,924 |
| `registry_seq012*` | local name registry for the | ~2,129 |

**pigeon_compiler/rename_engine/compliance_seq008/** - 7 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `compliance_seq008_helpers_seq002*` | auto extracted by pigeon compiler | ~227 |
| `compliance_seq008_classify_seq003*` | auto extracted by pigeon compiler | ~160 |
| `compliance_seq008_recommend_wrapper_seq006*` | auto extracted by pigeon compiler | ~603 |
| `compliance_seq008_audit_decomposed_seq007*` | auto extracted by pigeon compiler | ~638 |
| `compliance_seq008_audit_wrapper_seq009*` | auto extracted by pigeon compiler | ~653 |
| `compliance_seq008_check_file_seq010*` | auto extracted by pigeon compiler | ~311 |
| `compliance_seq008_format_report_seq011*` | auto extracted by pigeon compiler | ~320 |

**pigeon_compiler/runners/** - 9 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `run_compiler_test_seq007*` | self test pigeon compiler on | ~594 |
| `run_deepseek_plans_seq008*` | phase 2 send ether maps | ~587 |
| `run_pigeon_loop_seq009*` | the loop refactor until pigeon | ~2,836 |
| `run_clean_split_seq010*` | full clean pipeline deepseek plan | ~2,509 |
| `run_clean_split_helpers_seq011*` | helpers for run clean split | ~566 |
| `run_clean_split_init_seq012*` | init manifest writers for clean | ~1,663 |
| `manifest_bridge_seq013*` | update master manifest md after | ~1,016 |
| `reaudit_diff_seq014*` | re audit with diff across | ~1,732 |
| `run_batch_compile_seq015*` | compile entire codebase to pigeon | ~1,999 |

**pigeon_compiler/runners/compiler_output/press_release_gen/** - 8 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `press_release_gen_constants_seq001_v001_seq001*` | pigeon extracted by compiler | ~641 |
| `press_release_gen_template_builders_seq002_v001_seq001*` | pigeon extracted by compiler | ~626 |
| `press_release_gen_template_helpers_seq004_v001_seq001*` | pigeon extracted by compiler | ~661 |
| `press_release_gen_constants_seq001_v001_seq002*` | pigeon extracted by compiler | ~388 |
| `press_release_gen_template_builders_seq002_v001_seq002*` | pigeon extracted by compiler | ~662 |
| `press_release_gen_template_helpers_seq004_v001_seq002*` | pigeon extracted by compiler | ~296 |
| `press_release_gen_template_builders_seq002_v001_seq003*` | pigeon extracted by compiler | ~296 |
| `press_release_gen_template_key_findings_seq003*` | auto extracted by pigeon compiler | ~626 |

**pigeon_compiler/state_extractor/** - 6 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `ast_parser_seq001*` | parse python file into function | ~734 |
| `call_graph_seq002*` | build intra file call graph | ~847 |
| `import_tracer_seq003*` | trace imports inbound and outbound | ~792 |
| `shared_state_detector_seq004*` | detect module level shared state | ~618 |
| `resistance_analyzer_seq005*` | classify why a file resists | ~1,037 |
| `ether_map_builder_seq006*` | assemble full ether map json | ~697 |

**pigeon_compiler/weakness_planner/** - 1 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `deepseek_plan_prompt_seq004*` | build and send deepseek cut | ~2,407 |

**src/** - 28 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `timestamp_utils_seq001*` | millisecond epoch timestamp utility | ~156 |
| `models_seq002*` | dataclasses for keystroke events and | ~379 |
| `logger_seq003*` | core keystroke telemetry logger | ~1,636 |
| `context_budget_seq004*` | context budget scorer for llm | ~715 |
| `drift_watcher_seq005*` | drift detection for live llm | ~1,117 |
| `resistance_bridge_seq006*` | bridge between keystroke telemetry and | ~1,222 |
| `streaming_layer_seq007*` | monolithic live streaming interface for | ~10,189 |
| `.operator_stats_seq008*` | persistent markdown memory file | ~4,617 |
| `operator_stats_seq008*` | persistent markdown memory file | ~4,954 |
| `rework_detector_seq009*` | measures ai answer quality from | ~1,083 |
| `query_memory_seq010*` | recurring query detector unsaid thought | ~2,308 |
| `file_heat_map_seq011*` | tracks cognitive load per module | ~1,347 |
| `push_narrative_seq012*` | generate per push narrative each | ~2,089 |
| `push_narrative_seq012*` | generate per push narrative each | ~2,089 |
| `self_fix_seq013*` | one shot self fix analyzer | ~5,846 |
| `cognitive_reactor_seq014*` | cognitive reactor autonomous code modification | ~3,529 |
| `pulse_harvest_seq015*` | pulse harvest pairs prompts to | ~2,276 |
| `dynamic_prompt_seq017*` | steers copilot cot from live | ~3,996 |
| `dynamic_prompt_seq017*` | steers copilot cot from live | ~3,996 |
| `dynamic_prompt_seq017*` | steers copilot cot from live | ~4,458 |
| `task_queue_seq018*` | copilot driven task tracking linked | ~1,608 |
| `file_consciousness_seq019*` | ast derived function consciousness dating | ~4,343 |
| `copilot_prompt_manager_seq020*` | audits and manages all injected | ~4,488 |
| `mutation_scorer_seq021*` | mutation scorer correlates prompt mutations | ~1,611 |
| `rework_backfill_seq022*` | reconstructs historical rework scores from | ~1,198 |
| `session_handoff_seq023*` | session handoff summary generator | ~1,569 |
| `unsaid_recon_seq024*` | fires on high deletion prompts | ~1,112 |
| `push_cycle_seq025*` | the push is the unit | ~4,339 |

**src/cognitive/** - 3 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `adapter_seq001*` | cognitive state agent behavior adapter | ~1,264 |
| `unsaid_seq002*` | detects what operators meant but | ~2,108 |
| `drift_seq003*` | tracks operator typing patterns across | ~2,262 |

**src/cognitive/drift_seq003/** - 4 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `drift_seq003_baseline_store_seq001*` | auto extracted by pigeon compiler | ~299 |
| `drift_seq003_compute_baseline_seq002*` | auto extracted by pigeon compiler | ~557 |
| `drift_seq003_detect_session_drift_seq003*` | auto extracted by pigeon compiler | ~677 |
| `drift_seq003_build_cognitive_context_seq004*` | auto extracted by pigeon compiler | ~828 |

**src/cognitive/unsaid_seq002/** - 3 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `unsaid_seq002_helpers_seq001*` | auto extracted by pigeon compiler | ~561 |
| `unsaid_seq002_diff_seq002*` | auto extracted by pigeon compiler | ~245 |
| `unsaid_seq002_orchestrator_seq003*` | auto extracted by pigeon compiler | ~1,493 |

**src/cognitive_reactor_seq014/** - 12 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `cognitive_reactor_seq014_constants_seq001*` | auto extracted by pigeon compiler | ~95 |
| `cognitive_reactor_seq014_state_ops_seq002*` | auto extracted by pigeon compiler | ~146 |
| `cognitive_reactor_seq014_docstring_patch_seq003*` | auto extracted by pigeon compiler | ~563 |
| `cognitive_reactor_seq014_cognitive_hint_seq004*` | auto extracted by pigeon compiler | ~244 |
| `cognitive_reactor_seq014_patch_generator_seq005*` | auto extracted by pigeon compiler | ~781 |
| `cognitive_reactor_seq014_prompt_builder_seq006*` | auto extracted by pigeon compiler | ~25 |
| `cognitive_reactor_seq014_api_client_seq007*` | auto extracted by pigeon compiler | ~24 |
| `cognitive_reactor_seq014_reactor_core_seq008*` | auto extracted by pigeon compiler | ~1,026 |
| `cognitive_reactor_seq014_registry_loader_seq009*` | auto extracted by pigeon compiler | ~25 |
| `cognitive_reactor_seq014_self_fix_runner_seq010*` | auto extracted by pigeon compiler | ~25 |
| `cognitive_reactor_seq014_patch_writer_seq011*` | auto extracted by pigeon compiler | ~24 |
| `cognitive_reactor_seq014_decision_maker_seq012*` | auto extracted by pigeon compiler | ~25 |

**src/copilot_prompt_manager_seq020/** - 10 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `copilot_prompt_manager_seq020_constants_seq001*` | auto extracted by pigeon compiler | ~200 |
| `copilot_prompt_manager_seq020_block_utils_seq002*` | auto extracted by pigeon compiler | ~288 |
| `copilot_prompt_manager_seq020_json_utils_seq003*` | auto extracted by pigeon compiler | ~236 |
| `copilot_prompt_manager_seq020_operator_profile_seq004*` | auto extracted by pigeon compiler | ~472 |
| `copilot_prompt_manager_seq020_auto_index_seq005*` | auto extracted by pigeon compiler | ~665 |
| `copilot_prompt_manager_seq020_operator_state_decomposed_seq006*` | auto extracted by pigeon compiler | ~632 |
| `copilot_prompt_manager_seq020_telemetry_utils_seq007*` | auto extracted by pigeon compiler | ~329 |
| `copilot_prompt_manager_seq020_audit_decomposed_seq008*` | auto extracted by pigeon compiler | ~729 |
| `copilot_prompt_manager_seq020_injectors_seq009*` | auto extracted by pigeon compiler | ~461 |
| `copilot_prompt_manager_seq020_orchestrator_seq010*` | auto extracted by pigeon compiler | ~521 |

**src/file_consciousness_seq019/** - 12 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `file_consciousness_seq019_helpers_seq001*` | auto extracted by pigeon compiler | ~500 |
| `file_consciousness_seq019_persistence_seq002*` | auto extracted by pigeon compiler | ~149 |
| `file_consciousness_seq019_report_seq003*` | auto extracted by pigeon compiler | ~531 |
| `file_consciousness_seq019_audit_seq004*` | auto extracted by pigeon compiler | ~333 |
| `file_consciousness_seq019_derivation_seq005*` | auto extracted by pigeon compiler | ~649 |
| `file_consciousness_seq019_dependencies_seq006*` | auto extracted by pigeon compiler | ~503 |
| `file_consciousness_seq019_classify_seq007*` | auto extracted by pigeon compiler | ~222 |
| `file_consciousness_seq019_profile_builder_seq008*` | auto extracted by pigeon compiler | ~199 |
| `file_consciousness_seq019_main_orchestrator_seq009*` | auto extracted by pigeon compiler | ~269 |
| `file_consciousness_seq019_dating_decomposed_seq010*` | auto extracted by pigeon compiler | ~807 |
| `file_consciousness_seq019_dating_helpers_seq011*` | auto extracted by pigeon compiler | ~25 |
| `file_consciousness_seq019_dating_wrapper_seq012*` | auto extracted by pigeon compiler | ~806 |

**src/push_cycle_seq025/** - 8 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `push_cycle_seq025_constants_seq001*` | auto extracted by pigeon compiler | ~71 |
| `push_cycle_seq025_loaders_seq002*` | auto extracted by pigeon compiler | ~401 |
| `push_cycle_seq025_signal_extractors_seq003*` | auto extracted by pigeon compiler | ~614 |
| `push_cycle_seq025_sync_decomposed_seq004*` | auto extracted by pigeon compiler | ~624 |
| `push_cycle_seq025_coaching_seq005*` | auto extracted by pigeon compiler | ~554 |
| `push_cycle_seq025_moon_cycle_seq006*` | auto extracted by pigeon compiler | ~802 |
| `push_cycle_seq025_predictions_injector_decomposed_seq007*` | auto extracted by pigeon compiler | ~670 |
| `push_cycle_seq025_orchestrator_decomposed_seq008*` | auto extracted by pigeon compiler | ~613 |

**src/query_memory_seq010/** - 6 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `query_memory_seq010_constants_seq001*` | auto extracted by pigeon compiler | ~55 |
| `query_memory_seq010_fingerprint_seq002*` | auto extracted by pigeon compiler | ~134 |
| `query_memory_seq010_trigram_utils_seq003*` | auto extracted by pigeon compiler | ~138 |
| `query_memory_seq010_clustering_seq004*` | auto extracted by pigeon compiler | ~258 |
| `query_memory_seq010_record_query_seq005*` | auto extracted by pigeon compiler | ~452 |
| `query_memory_seq010_load_memory_decomposed_seq006*` | auto extracted by pigeon compiler | ~374 |

**src/self_fix_seq013/** - 11 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `self_fix_seq013_scan_hardcoded_seq001*` | auto extracted by pigeon compiler | ~428 |
| `self_fix_seq013_scan_query_noise_seq002*` | auto extracted by pigeon compiler | ~237 |
| `self_fix_seq013_scan_duplicate_docstrings_seq003*` | auto extracted by pigeon compiler | ~305 |
| `self_fix_seq013_scan_cross_file_coupling_seq004*` | auto extracted by pigeon compiler | ~519 |
| `self_fix_seq013_scan_over_hard_cap_decomposed_seq005*` | auto extracted by pigeon compiler | ~515 |
| `self_fix_seq013_scan_dead_exports_decomposed_seq006*` | auto extracted by pigeon compiler | ~678 |
| `self_fix_seq013_write_report_decomposed_seq007*` | auto extracted by pigeon compiler | ~593 |
| `self_fix_seq013_run_self_fix_decomposed_seq008*` | auto extracted by pigeon compiler | ~547 |
| `self_fix_seq013_auto_compile_oversized_decomposed_seq009*` | auto extracted by pigeon compiler | ~807 |
| `self_fix_seq013_seq_base_seq010*` | auto extracted by pigeon compiler | ~169 |
| `self_fix_seq013_auto_apply_import_fixes_decomposed_seq011*` | auto extracted by pigeon compiler | ~1,178 |

**streaming_layer/** - 19 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `streaming_layer_constants_seq001*` | auto extracted by pigeon compiler | ~261 |
| `streaming_layer_simulation_helpers_seq002*` | auto extracted by pigeon compiler | ~204 |
| `streaming_layer_dataclasses_seq004*` | pigeon extracted by compiler | ~717 |
| `streaming_layer_formatter_seq004*` | auto extracted by pigeon compiler | ~546 |
| `streaming_layer_connection_pool_seq005*` | auto extracted by pigeon compiler | ~969 |
| `streaming_layer_dataclasses_seq005*` | pigeon extracted by compiler | ~247 |
| `streaming_layer_aggregator_seq006*` | auto extracted by pigeon compiler | ~934 |
| `streaming_layer_dataclasses_seq006*` | pigeon extracted by compiler | ~154 |
| `streaming_layer_metrics_seq007*` | auto extracted by pigeon compiler | ~824 |
| `streaming_layer_alerts_seq008*` | auto extracted by pigeon compiler | ~1,371 |
| `streaming_layer_replay_seq009*` | auto extracted by pigeon compiler | ~932 |
| `streaming_layer_dashboard_seq010*` | auto extracted by pigeon compiler | ~858 |
| `streaming_layer_http_handler_seq011*` | auto extracted by pigeon compiler | ~1,182 |
| `streaming_layer_demo_functions_seq013*` | pigeon extracted by compiler | ~456 |
| `streaming_layer_demo_summary_seq013*` | auto extracted by pigeon compiler | ~365 |
| `streaming_layer_demo_functions_seq014*` | pigeon extracted by compiler | ~280 |
| `streaming_layer_demo_simulate_seq014*` | auto extracted by pigeon compiler | ~256 |
| `streaming_layer_orchestrator_seq016*` | pigeon extracted by compiler | ~1,408 |
| `streaming_layer_orchestrator_seq017*` | pigeon extracted by compiler | ~142 |

**Infrastructure (non-pigeon)**

| File | Folder |
|---|---|
| `_build_organism_health.py` | `(root)` |
| `_tmp_heal_check.py` | `(root)` |
| `_tmp_test_fixes.py` | `(root)` |
| `_tmp_test_reactor.py` | `(root)` |
| `autonomous_dev_stress_test.py` | `(root)` |
| `deep_test.py` | `(root)` |
| `stress_test.py` | `(root)` |
| `test_all.py` | `(root)` |
| `test_public_release.py` | `(root)` |
| `chat_composition_analyzer.py` | `client` |
| `chat_response_reader.py` | `client` |
| `composition_recon.py` | `client` |
| `os_hook.py` | `client` |
| `telemetry_cleanup.py` | `client` |
| `uia_reader.py` | `client` |
| `vscdb_poller.py` | `client` |
| `classify_bridge.py` | `vscode-extension` |
| `pulse_watcher.py` | `vscode-extension` |

<!-- /pigeon:auto-index -->
