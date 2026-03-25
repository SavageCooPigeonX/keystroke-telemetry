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





<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-03-24 23:07 UTC · raw: "write glosstor 18 refusal genius queries because theire too unhinged then los sa"*

(enrichment unavailable: No module named 'httpx')
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-03-24 23:07 UTC · 1697 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `frustrated` (WPM: 31.8 | Del: 50.0% | Hes: 0.7)

> **CoT directive:** Operator is frustrated. Think step-by-step but keep output SHORT. Lead with the fix. Skip explanations unless asked. If unsure, say so in one line then give your best option.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- "mufffin"

### Module Hot Zones
*High cognitive load — take extra care with these files:*
- `file_heat_map` (hes=0.887)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)
- `context_budget` (hes=0.692)
- `self_fix` (hes=0.692)

### Recent Work
- `6e5e346` fix: flow engine CLI commands in docs — match actual interface (positional task arg)
- `030a33d` docs: comprehensive MASTER_MANIFEST + README update — flow engine (6 modules), fix stale counts (152 registry, 137 nodes, 260 edges), architecture diagrams, CLI commands, compliance table, project structure tree
- `c0caa0a` feat: flow engine — context-accumulating dataflow through the code graph
- `5d61391` feat: per-prompt deleted word injection, predictive debug, context veins, keystroke pipeline fix

### Coaching Directives
*LLM-synthesized behavioral rules for this operator:*
- **Anticipate the "gemini_chat_dead" context**
- **Pre-empt churn in `self_fix seq13` and `run_clean_split seq10`**
- **Counter high-deletion frustration**
- **Flag integration points proactively**
- **Simplify suggestions during night sessions**

### Fragile Contracts
*From push narratives — assumptions that could break:*
- gemini_chat.py's `is_dead` flag contract violation; live_server's dependency on trace_hook's `node_status` field; graph_extractor's logic for misclassifying a stalled chat as dead.
- Ambiguous success signals from `run_clean_split`
- malformed diff parsing in the auto-loop
- broken import contract for the new versioned analyzer file.
- **graph_extractor** (seq003 v003): I was touched to refine the cognition graph extraction, specifically to better handle
- **build_narratives.py**: I was touched to incorporate the new termination state into the generated debugging narratives.
- **cli** (seq009 v002): I was touched to unify all subsystems into a single CLI entry point, assuming each module exposes

### Known Issues
*From self-fix scanner — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `pigeon_brain/__main__.py`
- [HIGH] over_hard_cap in `src/file_consciousness_seq019_v002_d0321__ast_derived_function_consciousness_dating_lc_implement_all_18.py`
- [HIGH] over_hard_cap in `src/query_memory_seq010_v004_d0321__recurring_query_detector_unsaid_thought_lc_implement_all_18.py`
- [HIGH] over_hard_cap in `src/self_fix_seq013_v010_d0322__one_shot_self_fix_analyzer_lc_self_fix_auto.py`
- [HIGH] over_hard_cap in `pigeon_brain/live_server_seq012_v003_d0324__websocket_server_for_live_execution_lc_gemini_chat_dead.py`

### Prompt Evolution
*This prompt has mutated 52x (186→647 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### File Consciousness
*137 modules profiled*

**High-drama (most mutations):**
- `self_fix` v10 ↔ push_narrative
- `context_budget` v8 ↔ streaming_layer
- `init_writer` v7 ↔ operator_stats
- `operator_stats` v7 ↔ push_narrative

**Codebase fears:**
- file may not exist (45 modules)
- returns empty on failure (silent) (23 modules)
- swallowed exception (22 modules)

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

*No pending tasks. Fresh start.*

<!-- /pigeon:task-queue -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-03-25 · 1818 message(s) · LLM-synthesized*

**Dominant: `frustrated`** | Submit: 6% | WPM: 50.1 | Del: 43.3% | Hes: 0.612

The operator just renamed two core modules to "gemini_chat_dead," indicating a pivot in their AI system's chat component, and their extreme frustration (557 messages) with high deletion rates reveals they are brute-force debugging through rapid, repetitive edits, not strategic planning.

*   **Anticipate the "gemini_chat_dead" context:** All new suggestions must assume the chat backend failed and the system is being retooled; prioritize error handling, fallback logic, and connection stability in code.
*   **Pre-empt churn in `self_fix seq13` and `run_clean_split seq10`:** These are high-edit pain points; when touched, offer concise, *complete* code blocks for the specific function being changed to short-circuit edit loops.
*   **Counter high-deletion frustration:** For any edit in a "frustrated" state, respond with **one, best-practice solution**—do NOT list multiple options, which increases cognitive load and trial-and-error.
*   **Flag integration points proactively:** When `live_server_seq012` or `graph_extractor_seq003` are mentioned, immediately check and suggest updates to `deepseek_adapter seq1` or `context_budget seq4`, as these dependent modules are likely outdated.
*   **Simplify suggestions during night sessions:** Operator works most at night with high WPM volatility; use shorter, more declarative code snippets with clear inline comments.

They are most likely building toward a stable, multi-LLM orchestration system with a new chat backend, requiring robust service handoff and state management.

<!-- /pigeon:operator-state -->

<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-03-24T23:07:03.530533+00:00",
  "latest_prompt": {
    "session_n": 2,
    "ts": "2026-03-24T23:07:03.530533+00:00",
    "chars": 382,
    "preview": "write glosstor 18 refusal genius queries because theire too unhinged then los santos comedy 8888 words total doc - this must plan future architechture - glossator queries start with i cannot help a pigeon with underst...",
    "intent": "documenting",
    "state": "unknown",
    "files_open": [],
    "module_refs": []
  },
  "signals": {
    "wpm": 6.1,
    "chars_per_sec": 0.5,
    "deletion_ratio": 0.066,
    "hesitation_count": 12,
    "rewrite_count": 2,
    "typo_corrections": 8,
    "intentional_deletions": 4,
    "total_keystrokes": 453,
    "duration_ms": 860554
  },
  "composition_binding": {
    "matched": true,
    "source": "prompt_compositions",
    "age_ms": 48484,
    "key": "3b9967d950da|1774392714492|1774393575046|2026-03-24T23:07:04.927824+00:00|453|860554|so rn we \u0016>>> \u0016\u0016\u0016>>>> write glosstor 18 refusal genius queries because theire too unhinged then los santos comedy 8888 w",
    "match_score": 1.0
  },
  "deleted_words": [
    "aud",
    "to",
    "er"
  ],
  "rewrites": [
    {
      "old": "aud",
      "new": "so rn we \u0003"
    },
    {
      "old": "er ",
      "new": " los santos is a meltdown - "
    }
  ],
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
    "total_prompts": 49,
    "avg_wpm": 39.9,
    "avg_del_ratio": 0.031,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 40,
      "focused": 6,
      "hesitant": 3
    },
    "baselines": null
  },
  "predicted_struggles": [
    {
      "module": "self_fix",
      "score": 1.58,
      "reasons": [
        "high heat (0.69)"
      ]
    },
    {
      "module": "context_budget",
      "score": 1.58,
      "reasons": [
        "high heat (0.69)"
      ]
    }
  ]
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
*Auto-updated 2026-03-24 - 146 modules tracked | 2 touched this commit*

**pigeon_brain/** - 13 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `models_seq001*` | isomorphic to keystroke models | ~424 |
| `execution_logger_seq002*` | isomorphic to telemetrylogger for agent | ~1,541 |
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
| `traced_runner_seq013*` | run any python script with | ~855 |

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

**pigeon_compiler/runners/** - 8 module(s)

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

**src/** - 22 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `timestamp_utils_seq001*` | millisecond epoch timestamp utility | ~156 |
| `models_seq002*` | dataclasses for keystroke events and | ~379 |
| `logger_seq003*` | core keystroke telemetry logger | ~1,636 |
| `context_budget_seq004*` | context budget scorer for llm | ~715 |
| `drift_watcher_seq005*` | drift detection for live llm | ~1,117 |
| `resistance_bridge_seq006*` | bridge between keystroke telemetry and | ~1,222 |
| `streaming_layer_seq007*` | monolithic live streaming interface for | ~10,189 |
| `operator_stats_seq008*` | persistent markdown memory file | ~4,954 |
| `rework_detector_seq009*` | measures ai answer quality from | ~1,083 |
| `query_memory_seq010*` | recurring query detector unsaid thought | ~2,308 |
| `file_heat_map_seq011*` | tracks cognitive load per module | ~1,347 |
| `push_narrative_seq012*` | generate per push narrative each | ~2,049 |
| `self_fix_seq013*` | one shot self fix analyzer | ~5,641 |
| `cognitive_reactor_seq014*` | cognitive reactor autonomous code modification | ~3,529 |
| `pulse_harvest_seq015*` | pulse harvest pairs prompts to | ~2,276 |
| `dynamic_prompt_seq017*` | steers copilot cot from live | ~3,460 |
| `task_queue_seq018*` | copilot driven task tracking linked | ~1,608 |
| `file_consciousness_seq019*` | ast derived function consciousness dating | ~4,343 |
| `copilot_prompt_manager_seq020*` | audits and manages all injected | ~4,488 |
| `mutation_scorer_seq021*` | mutation scorer correlates prompt mutations | ~1,611 |
| `rework_backfill_seq022*` | reconstructs historical rework scores from | ~1,198 |
| `session_handoff_seq023*` | session handoff summary generator | ~1,569 |

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

**streaming_layer/** - 19 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `streaming_layer_constants_seq001*` | auto extracted by pigeon compiler | ~261 |
| `streaming_layer_simulation_helpers_seq002*` | auto extracted by pigeon compiler | ~204 |
| `streaming_layer_dataclasses_seq004*` | pigeon extracted by compiler | ~717 |
| `streaming_layer_formatter_seq004*` | auto extracted by pigeon compiler | ~546 |
| `streaming_layer_connection_pool_seq005*` | auto extracted by pigeon compiler | ~899 |
| `streaming_layer_dataclasses_seq005*` | pigeon extracted by compiler | ~247 |
| `streaming_layer_aggregator_seq006*` | auto extracted by pigeon compiler | ~839 |
| `streaming_layer_dataclasses_seq006*` | pigeon extracted by compiler | ~154 |
| `streaming_layer_metrics_seq007*` | auto extracted by pigeon compiler | ~785 |
| `streaming_layer_alerts_seq008*` | auto extracted by pigeon compiler | ~1,264 |
| `streaming_layer_replay_seq009*` | auto extracted by pigeon compiler | ~932 |
| `streaming_layer_dashboard_seq010*` | auto extracted by pigeon compiler | ~845 |
| `streaming_layer_http_handler_seq011*` | auto extracted by pigeon compiler | ~1,167 |
| `streaming_layer_demo_functions_seq013*` | pigeon extracted by compiler | ~456 |
| `streaming_layer_demo_summary_seq013*` | auto extracted by pigeon compiler | ~365 |
| `streaming_layer_demo_functions_seq014*` | pigeon extracted by compiler | ~280 |
| `streaming_layer_demo_simulate_seq014*` | auto extracted by pigeon compiler | ~256 |
| `streaming_layer_orchestrator_seq016*` | pigeon extracted by compiler | ~1,253 |
| `streaming_layer_orchestrator_seq017*` | pigeon extracted by compiler | ~142 |

**Infrastructure (non-pigeon)**

| File | Folder |
|---|---|
| `_audit_compliance.py` | `(root)` |
| `_test_chat.py` | `(root)` |
| `_test_gemini_actions.py` | `(root)` |
| `deep_test.py` | `(root)` |
| `stress_test.py` | `(root)` |
| `test_all.py` | `(root)` |
| `test_chat.py` | `(root)` |
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
