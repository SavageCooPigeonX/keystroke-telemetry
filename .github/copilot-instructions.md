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

*Fresh start -- no telemetry data yet.*

<!-- /pigeon:task-context -->

<!-- pigeon:task-queue -->
## Active Task Queue

*No pending tasks. Fresh start.*

<!-- /pigeon:task-queue -->
<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-03-21 15:57 UTC · 243 messages profiled · 8 recent commits*

**Current focus:** building new features
**Cognitive state:** `hesitant` (WPM: 56759.9 | Del: 36.5% | Hes: 0.519)

> **CoT directive:** Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- "rrectuui"
- "sureher co"

### Module Hot Zones
*High cognitive load — take extra care with these files:*
- `file_heat_map` (hes=0.887)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)
- `context_budget` (hes=0.438)
- `push_narrative` (hes=0.438)

### AI Rework Surface
*Miss rate: 100.0% (1 responses)*
- Failed on: ""

### Recent Work
- `e809454` feat: self-calibrating cognitive state classification
- `482bd07` feat: repo cleanup + enriched journal + deep README/MANIFEST update
- `21ddf89` feat: task queue system + AI response capture plan + README update
- `ec35e10` docs: full README rewrite â€” all three systems documented

### Coaching Directives
*LLM-synthesized behavioral rules for this operator:*
- **Intervene on hesitation**
- **Anticipate recurring pain in the coaching pipeline modules**
- **Counter high rework**
- **Break the frustration cycle**
- **Structure the next step**

### Fragile Contracts
*From push narratives — assumptions that could break:*
- operator_stats’s error-rate calculation for self-calibration; classify_bridge’s dependency on a pull-based cognitive state API; prompt_journal’s non-atomic writes in forked processes.
- prompt_journal path assumptions
- hardcoded imports to removed zero-token modules
- telemetry breaks from missing operator_stats file. This push accomplishes a repository cleanup by removing obsolete or placeholder code while retaining the core prompt journal.
- push_narrative's assumption of `prompt_recon_attempts` telemetry key; git_plugin's prefix-based intent parsing; prompt_recon_seq016_v001's dependency on unified diff format. This push introduces automated prompt reconstruction and enhances push narratives with structured telemetry and chat analysis.
- **operator_stats** speaks: I was touched to embed a self-calibrating cognitive layer, shifting from passive logging to a
- **operator_stats_seq008_v004_d0317__persistent_markdown_memory_file_lc_dynamic_task_context** speaks: I was created as a
- **prompt_journal_seq019_v001** speaks: I was added as a new journal file to capture the reasoning behind this self-calib
- **classify_bridge** speaks: I was likely updated to integrate with the new cognitive calibration, probably to receive ad
- **push_narrative** (seq012 v005) speaks: I was touched to implement a new narrative generation mode, "generate_per_push_
- **chat_composition_analyzer** speaks: I was added as a new client module to parse chat logs and extract structured metad

### Known Issues
*From self-fix scanner — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `stress_test.py`
- [CRITICAL] hardcoded_import in `test_all.py`
- [CRITICAL] hardcoded_import in `vscode-extension/pulse_watcher.py`

### Prompt Evolution
*This prompt has mutated 30x (186→518 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, prompt_recon, file_consciousness.*

### File Consciousness
*83 modules profiled*

**High-drama (most mutations):**
- `context_budget` v7 ↔ streaming_layer
- `operator_stats` v5 ↔ push_narrative
- `push_narrative` v5 ↔ operator_stats
- `file_writer` v4 ↔ resplit_binpack

**Codebase fears:**
- file may not exist (21 modules)
- regex format dependency (10 modules)
- swallowed exception (9 modules)

**Slumber party warnings (high coupling):**
- `file_writer` ↔ `resplit_binpack` (score=0.80, 3 shared imports, both high-churn (v4+v4))
- `file_writer` ↔ `resplit` (score=0.80, 3 shared imports, both high-churn (v4+v4))
- `func_decomposer` ↔ `run_clean_split` (score=0.80, 3 shared imports, both high-churn (v4+v4))

<!-- /pigeon:task-context -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-03-21 - 252 message(s) in profile*

**Dominant: `frustrated`** | Submit: 17% | WPM: 662778.9 | Del: 32.5% | Hes: 0.536

**Behavioral tunes for this session:**
- **frustrated** -> concise answers, 2-3 options max, bullets, lead with solution
- Deletion ratio > 30% -> high rethinking; consider asking "what specifically do you need?"
- Submit rate 17% -> messages often abandoned; check if previous answer landed before going deep
- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples
- Active hours: 0:00(17), 2:00(3), 3:00(6), 4:00(27), 5:00(18), 6:00(38), 7:00(45), 15:00(7), 16:00(11), 17:00(21), 18:00(8), 20:00(2), 21:00(9), 22:00(26), 23:00(14)
<!-- /pigeon:operator-state -->
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-03-21T15:57:29.581033+00:00",
  "latest_prompt": {
    "session_n": 3,
    "ts": "2026-03-21T15:57:29.581033+00:00",
    "chars": 59,
    "preview": "push and test rename of pigeon - make sure api is connected",
    "intent": "building",
    "state": "unknown",
    "files_open": [
      "logs/copilot_prompt_mutations.json"
    ],
    "module_refs": []
  },
  "signals": {
    "wpm": 54.0,
    "chars_per_sec": 4.5,
    "deletion_ratio": 0.0,
    "hesitation_count": 0,
    "rewrite_count": 0,
    "typo_corrections": 0,
    "intentional_deletions": 0,
    "total_keystrokes": 60,
    "duration_ms": 13331
  },
  "composition_binding": {
    "matched": true,
    "source": "prompt_compositions",
    "age_ms": 26751,
    "key": "c6089014481d|1774108609499|1774108622830|2026-03-21T15:57:30.098018+00:00|60|13331|push and test rename of pigeon - make sure api is connected ",
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
    "total_prompts": 21,
    "avg_wpm": 40.0,
    "avg_del_ratio": 0.033,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 14,
      "focused": 5,
      "hesitant": 2
    },
    "baselines": null
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
*Auto-updated 2026-03-21 - 96 modules tracked | 1 touched this commit*

**pigeon_compiler/bones/** - 5 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `aim_utils_seq001*` | extracted from hush aim py | ~724 |
| `core_formatters_seq001*` | extracted from hush chat core | ~1,291 |
| `nl_parsers_seq001*` | extracted from hush nl detection | ~1,844 |
| `pq_manifest_utils_seq001*` | extracted from hush pre query | ~879 |
| `pq_search_utils_seq001*` | extracted from hush pre query | ~3,279 |

**pigeon_compiler/cut_executor/** - 11 module(s)

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

**pigeon_compiler/integrations/** - 1 module(s)

| Search pattern | Desc | Tokens |
|---|---|---:|
| `deepseek_adapter_seq001*` | deepseek api client | ~1,177 |

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

**pigeon_compiler/runners/** - 8 module(s)

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
| `logger_seq003*` | core keystroke telemetry logger | ~1,542 |
| `context_budget_seq004*` | context budget scorer for llm | ~703 |
| `drift_watcher_seq005*` | drift detection for live llm | ~1,117 |
| `resistance_bridge_seq006*` | bridge between keystroke telemetry and | ~1,222 |
| `streaming_layer_seq007*` | monolithic live streaming interface for | ~10,189 |
| `operator_stats_seq008*` | persistent markdown memory file | ~4,807 |
| `rework_detector_seq009*` | measures ai answer quality from | ~1,083 |
| `query_memory_seq010*` | recurring query detector unsaid thought | ~2,308 |
| `file_heat_map_seq011*` | tracks cognitive load per module | ~1,347 |
| `push_narrative_seq012*` | generate per push narrative each | ~2,049 |
| `self_fix_seq013*` | one shot self fix analyzer | ~4,354 |
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