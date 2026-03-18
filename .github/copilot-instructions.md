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
3. **Dynamic Prompt Layer** — task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations) and generates a context block that steers how Copilot reasons. Self-updates on every commit via `<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-03-17 07:04 UTC · 161 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `hesitant` (WPM: 41.2 | Del: 34.5% | Hes: 0.507)

> **CoT directive:** Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- "strews"

### Module Hot Zones
*High cognitive load — take extra care with these files:*
- `context_budget` (hes=0.92)
- `file_heat_map` (hes=0.92)
- `push_narrative` (hes=0.92)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)

### AI Rework Surface
*Miss rate: 100.0% (1 responses)*
- Failed on: ""

### Recent Work
- `21ddf89` feat: task queue system + AI response capture plan + README update
- `ec35e10` docs: full README rewrite â€” all three systems documented
- `5f3fa22` docs: rebuild all manifests + MASTER_MANIFEST + CHANGELOG patch notes
- `f989307` feat: wire narratives + self-fix + coaching + gaps into dynamic prompt injection

### Fragile Contracts
*From push narratives — assumptions that could break:*
- push_narrative's assumption of `prompt_recon_attempts` telemetry key; git_plugin's prefix-based intent parsing; prompt_recon_seq016_v001's dependency on unified diff format. This push introduces automated prompt reconstruction and enhances push narratives with structured telemetry and chat analysis.
- git_plugin's string type assumption for mutated prompts
- prompt_recon_seq016_v001's fragile string parsing of code blocks
- the implicit contract of the mutation function signature between the two files.
- 1) Commit intent field parsing fails
- **push_narrative** (seq012 v005) speaks: I was touched to implement a new narrative generation mode, "generate_per_push_
- **chat_composition_analyzer** speaks: I was added as a new client module to parse chat logs and extract structured metad
- **git_plugin** speaks: I was modified to expose a new method `get_commit_intent` that extracts the intent from a commit 
- **prompt_recon_seq016_v001** speaks: I am a new prompt reconstruction sequence, invoked to rebuild prompts from commit h
- **push_narrative_seq012_v004_d0317__generate_per_push_narrative_each_lc_pulse_telemetry_prompt** speaks: I am a newly cr
- **git_plugin** was touched to integrate a new prompt mutation system, requiring the addition of a `_mutate_prompt` metho

### Known Issues
*From self-fix scanner — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `stress_test.py`
- [CRITICAL] hardcoded_import in `test_all.py`
- [CRITICAL] hardcoded_import in `vscode-extension/pulse_watcher.py`
- [HIGH] query_noise

### Persistent Gaps
*Recurring queries — operator keeps hitting these:*
- [3x] call deepseek scope verify

### Prompt Evolution
*This prompt has mutated 26x (186→391 lines). Features added: auto_index, operator_state, prompt_journal, pulse_blocks.*

<!-- /pigeon:task-context -->

<!-- pigeon:task-queue -->
## Active Task Queue

*Copilot manages this queue. To complete a task: update the referenced MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*

### Pending
- [ ] `tq-001` **Fix hardcoded pigeon import in `test_all.py`** | stage: debugging | focus: `test_all.py`
  → [MASTER_MANIFEST.md](MASTER_MANIFEST.md)
- [ ] `tq-002` **Fix hardcoded pigeon import in `stress_test.py`** | stage: debugging | focus: `stress_test.py`
  → [MASTER_MANIFEST.md](MASTER_MANIFEST.md)
- [ ] `tq-003` **Implement AI response capture via UIA** | stage: implementing | focus: `vscode-extension/src/extension.ts`, `src/rework_detector_seq009*`
  → [src/MANIFEST.md](src/MANIFEST.md)
- [ ] `tq-004` **Pigeon compile `operator_stats_seq008` (397 lines → compliant)** | stage: planning | focus: `src/operator_stats_seq008*`
  → [src/MANIFEST.md](src/MANIFEST.md)
- [ ] `tq-005` **Pigeon compile `self_fix_seq013` (352 lines → compliant)** | stage: planning | focus: `src/self_fix_seq013*`
  → [src/MANIFEST.md](src/MANIFEST.md)
- [ ] `tq-006` **Wire response capture into rework_log (prompt→response→rework triples)** | stage: planning | focus: `src/rework_detector_seq009*`, `logs/ai_responses.jsonl`
  → [src/MANIFEST.md](src/MANIFEST.md)
*…and 4 more in `task_queue.json`*

<!-- /pigeon:task-queue -->

<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-03-18 · 1023 message(s) · LLM-synthesized*

**Dominant: `frustrated`** | Submit: 1% | WPM: 396.7 | Del: 39.5% | Hes: 0.964

This operator just built a Copilot-driven task tracking system and their high-deletion, hesitant-frustrated-abandoned cycling reveals they're struggling with architectural clarity and implementation precision during late-night sessions.

- **When they edit task_queue_system files**, immediately propose concrete, small-scope helper functions (like `_log_task_transition()` or `_validate_queue_state()`) instead of broad architectural suggestions.
- **Anticipate churn in `push_narrative` and `context_budget` modules**—they're adjacent to the new task system; proactively offer to update cross-references or import statements there when you see changes to task_queue files.
- **Given the 100% miss rate**, after any code suggestion, immediately follow with: "Should I also check the `import_fixer` or `init_writer` modules for consistency with this change?" This preempts rework.
- **When you detect slow WPM with high deletions (frustrated/hesitant state)**, respond with one-line, copy-paste-ready code blocks—avoid multi-option lists.
- **Explicitly bridge gaps** by linking new task_queue functions to existing patterns in `func_decomposer` or `plan_parser` modules to reduce cognitive load.

They are most likely building toward a unified, LLM-orchestrated workflow engine that connects task tracking, context management, and automated documentation.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `os_hook`** (hes=0.959, state=frustrated). Simplify interactions with this module.

> **Cognitive reactor fired on `os_hook`** (hes=0.943, state=frustrated). Simplify interactions with this module.

> **Cognitive reactor fired on `os_hook`** (hes=1.0, state=frustrated). Simplify interactions with this module.

> **Cognitive reactor fired on `os_hook`** (hes=0.948, state=frustrated). Simplify interactions with this module.

> **Cognitive reactor fired on `os_hook`** (hes=1.038, state=frustrated). Simplify interactions with this module.

> **Cognitive reactor fired on `operator_stats`** (hes=1.0, state=hesitant). Simplify interactions with this module.


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
*Auto-updated 2026-03-17 — 91 modules tracked | 1 touched this commit*

**pigeon_compiler/bones/** — 5 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `aim_utils_seq001*` | extracted from hush aim py | ~724 |
| `core_formatters_seq001*` | extracted from hush chat core | ~1,291 |
| `nl_parsers_seq001*` | extracted from hush nl detection | ~1,844 |
| `pq_manifest_utils_seq001*` | extracted from hush pre query | ~879 |
| `pq_search_utils_seq001*` | extracted from hush pre query | ~3,279 |

**pigeon_compiler/cut_executor/** — 11 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `plan_parser_seq001*` | parse deepseek json from raw | ~371 |
| `source_slicer_seq002*` | extract functions constants from source | ~486 |
| `file_writer_seq003*` | write new pigeon compliant files | ~747 |
| `import_fixer_seq004*` | update imports across the project | ~505 |
| `manifest_writer_seq005*` | generate manifest md for a | ~448 |
| `plan_validator_seq006*` | validate cut plan before execution | ~579 |
| `init_writer_seq007*` | generate init py for split | ~361 |
| `func_decomposer_seq008*` | decompose oversized functions via deepseek | ~639 |
| `resplit_seq009*` | deterministic ast bin packing re | ~841 |
| `resplit_binpack_seq010*` | bin packing file writing for | ~702 |
| `resplit_helpers_seq011*` | shared helpers for re splitter | ~501 |

**pigeon_compiler/integrations/** — 1 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `deepseek_adapter_seq001*` | deepseek api client | ~1,177 |

**pigeon_compiler/rename_engine/** — 12 module(s)

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

**pigeon_compiler/runners/** — 8 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `run_compiler_test_seq007*` | self test pigeon compiler on | ~594 |
| `run_deepseek_plans_seq008*` | phase 2 send ether maps | ~587 |
| `run_pigeon_loop_seq009*` | the loop refactor until pigeon | ~2,836 |
| `run_clean_split_seq010*` | full clean pipeline deepseek plan | ~2,226 |
| `run_clean_split_helpers_seq011*` | helpers for run clean split | ~566 |
| `run_clean_split_init_seq012*` | init manifest writers for clean | ~1,663 |
| `manifest_bridge_seq013*` | update master manifest md after | ~1,016 |
| `reaudit_diff_seq014*` | re audit with diff across | ~1,732 |

**pigeon_compiler/runners/compiler_output/press_release_gen/** — 8 module(s)

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

**pigeon_compiler/state_extractor/** — 6 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `ast_parser_seq001*` | parse python file into function | ~734 |
| `call_graph_seq002*` | build intra file call graph | ~847 |
| `import_tracer_seq003*` | trace imports inbound and outbound | ~792 |
| `shared_state_detector_seq004*` | detect module level shared state | ~618 |
| `resistance_analyzer_seq005*` | classify why a file resists | ~1,037 |
| `ether_map_builder_seq006*` | assemble full ether map json | ~697 |

**pigeon_compiler/weakness_planner/** — 1 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `deepseek_plan_prompt_seq004*` | build and send deepseek cut | ~2,407 |

**src/** — 17 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `timestamp_utils_seq001*` | millisecond epoch timestamp utility | ~147 |
| `models_seq002*` | dataclasses for keystroke events and | ~379 |
| `logger_seq003*` | core keystroke telemetry logger | ~1,539 |
| `context_budget_seq004*` | context budget scorer for llm | ~703 |
| `drift_watcher_seq005*` | drift detection for live llm | ~988 |
| `resistance_bridge_seq006*` | bridge between keystroke telemetry and | ~1,222 |
| `streaming_layer_seq007*` | monolithic live streaming interface for | ~10,189 |
| `operator_stats_seq008*` | persistent markdown memory file | ~3,616 |
| `rework_detector_seq009*` | measures ai answer quality from | ~1,047 |
| `query_memory_seq010*` | recurring query detector unsaid thought | ~1,122 |
| `file_heat_map_seq011*` | tracks cognitive load per module | ~1,347 |
| `push_narrative_seq012*` | generate per push narrative each | ~2,049 |
| `self_fix_seq013*` | one shot self fix analyzer | ~3,205 |
| `cognitive_reactor_seq014*` | cognitive reactor autonomous code modification | ~2,844 |
| `pulse_harvest_seq015*` | pulse harvest pairs prompts to | ~2,009 |
| `dynamic_prompt_seq017*` | steers copilot cot from live | ~2,947 |
| `task_queue_seq018*` | copilot driven task tracking linked | ~1,608 |

**src/cognitive/** — 3 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `adapter_seq001*` | cognitive state agent behavior adapter | ~1,264 |
| `unsaid_seq002*` | detects what operators meant but | ~2,108 |
| `drift_seq003*` | tracks operator typing patterns across | ~2,262 |

**streaming_layer/** — 19 module(s)

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

<!-- /pigeon:auto-index -->
