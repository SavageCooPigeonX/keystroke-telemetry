# MASTER_MANIFEST.md — keystroke-telemetry
**Version**: v0.2.0 | **Last Updated**: 2026-03-11

---

## 📦 PROJECT OVERVIEW

Cognitive-sync keystroke telemetry for LLM interfaces. Captures typing patterns,
computes hesitation scores, feeds resistance signals into the Pigeon Code Compiler,
and provides live streaming dashboards for real-time operator analysis.

**Stack**: Python 3.11+ stdlib (core) + httpx (compiler DeepSeek calls)
**Schema**: `keystroke_telemetry/v2` — self-contained JSON blocks per event
**Compiler**: Pigeon Code Compiler v0.2.0 — DeepSeek-powered AST splitter

---

## 🗂️ FOLDER TREE

```
keystroke-telemetry/
│
├── src/                                           # Core telemetry library
│   ├── __init__.py                                #   Package root
│   ├── timestamp_utils_seq001_v001.py             #   ms-epoch utility (8 lines)
│   ├── models_seq002_v001.py                      #   KeyEvent + MessageDraft (31 lines)
│   ├── logger_seq003_v001.py                      #   Core logger, v2 schema (143 lines)
│   ├── context_budget_seq004_v001.py              #   LLM-aware file sizing (80 lines)
│   ├── drift_watcher_seq005_v001.py               #   Live drift detection (95 lines)
│   ├── resistance_bridge_seq006_v001.py           #   Telemetry → compiler signal (111 lines)
│   └── streaming_layer_seq007_v001.py             #   Monolith — compiler test input (1142 lines)
│
├── streaming_layer/                               # Pigeon-compiled output from seq007
│   ├── __init__.py                                #   Re-exports all 27 public names
│   ├── streaming_layer_constants_seq001_v001.py   #   Constants + config (44 lines) ✅
│   ├── streaming_layer_*_seq002-017_v001.py       #   18 extracted modules
│   ├── MANIFEST.md                                #   Subfolder manifest + prompt box
│   └── (20 files total, 10 ≤50 lines, 10 single-class files)
│
├── pigeon_compiler/                               # The compiler itself (embedded, bugfixed)
│   ├── state_extractor/                           #   Layer 1: AST, call graph, resistance
│   │   ├── ast_parser_seq001_v001.py              #     Parse → functions, classes, constants
│   │   ├── call_graph_seq002_v001.py              #     Who calls whom
│   │   ├── import_tracer_seq003_v001.py           #     Outbound + inbound imports
│   │   ├── shared_state_detector_seq004_v001.py   #     Module-level state detection
│   │   ├── resistance_analyzer_seq005_v001.py     #     Coupling + resistance scoring
│   │   └── ether_map_builder_seq006_v001.py       #     Orchestrate Layer 1 → ether map
│   │
│   ├── weakness_planner/                          #   Layer 2: DeepSeek cut planning
│   │   └── deepseek_plan_prompt_seq004_v001.py    #     Build prompt, send, validate
│   │
│   ├── cut_executor/                              #   Layer 3: Deterministic execution
│   │   ├── plan_parser_seq001_v001.py             #     Parse DeepSeek JSON response
│   │   ├── source_slicer_seq002_v001.py           #     Extract funcs/classes by name
│   │   ├── file_writer_seq003_v001.py             #     Write pigeon-compliant files
│   │   ├── import_fixer_seq004_v001.py            #     Resolve imports per file
│   │   ├── manifest_writer_seq005_v001.py         #     Generate subfolder MANIFEST.md
│   │   ├── plan_validator_seq006_v001.py          #     Validate plan before execution
│   │   ├── init_writer_seq007_v001.py             #     Generate __init__.py re-exports
│   │   ├── func_decomposer_seq008_v001.py         #     Decompose >50-line functions
│   │   ├── resplit_seq009_v001.py                 #     Deterministic AST re-splitter
│   │   ├── resplit_binpack_seq010_v001.py         #     First-fit-decreasing bin packer
│   │   └── resplit_helpers_seq011_v001.py         #     Shared resplit utilities
│   │
│   ├── runners/                                   #   Pipeline orchestrators
│   │   ├── run_clean_split_seq010_v001.py         #     Full 6-phase pipeline
│   │   ├── run_clean_split_helpers_seq011_v001.py #     Phase 1 decomposition
│   │   ├── run_clean_split_init_seq012_v001.py    #     Phase 5 init + manifest
│   │   ├── manifest_bridge_seq013_v001.py         #     Phase 6 master manifest update
│   │   └── reaudit_diff_seq014_v001.py            #     Re-audit after changes
│   │
│   ├── integrations/
│   │   └── deepseek_adapter.py                    #     DeepSeek API with retry + timeout
│   │
│   ├── bones/                                     #   Shared utilities
│   ├── docs/                                      #   Design documents
│   └── output/                                    #   Cached ether maps + plans
│
├── test_all.py                                    # Test suite (221 lines, 4 tests, ALL PASS)
├── test_logs/                                     # Test session artifacts
├── demo_logs/                                     # Demo session artifacts
├── README.md                                      # Project readme
├── MASTER_MANIFEST.md                             # This file
└── .gitignore
```

---

## 📊 MODULE INVENTORY

### src/ — Core Telemetry (7 modules, 1615 total lines)

| File | Lines | Role | Exports |
|------|-------|------|---------|
| `timestamp_utils_seq001_v001.py` | 8 | Utility | `_now_ms` |
| `models_seq002_v001.py` | 31 | Data models | `KeyEvent`, `MessageDraft` |
| `logger_seq003_v001.py` | 143 | Core logger | `TelemetryLogger`, `SCHEMA_VERSION` |
| `context_budget_seq004_v001.py` | 80 | Budget scorer | `score_context_budget`, `estimate_tokens` |
| `drift_watcher_seq005_v001.py` | 95 | Drift detection | `DriftWatcher` |
| `resistance_bridge_seq006_v001.py` | 111 | Compiler bridge | `HesitationAnalyzer` |
| `streaming_layer_seq007_v001.py` | 1142 | Monolith (test) | 8 classes, ~15 functions |

### streaming_layer/ — Compiled Output (20 files, 1184 total lines)

| File | Lines | Status | Exports |
|------|-------|--------|---------|
| `streaming_layer_constants_seq001_v001.py` | 44 | ✅ | 14 constants |
| `streaming_layer_simulation_helpers_seq002_v001.py` | 20 | ✅ | `_sim_type`, `_sim_backspace` |
| `streaming_layer_dataclasses_seq004_v001.py` | 76 | 🔴 class | `AggregationBucket` |
| `streaming_layer_dataclasses_seq005_v001.py` | 23 | ✅ | `StreamClient` |
| `streaming_layer_dataclasses_seq006_v001.py` | 13 | ✅ | `Alert` |
| `streaming_layer_formatter_seq004_v001.py` | 57 | 🔴 class | `StreamFormatter` |
| `streaming_layer_connection_pool_seq005_v001.py` | 99 | 🔴 class | `ConnectionPool` |
| `streaming_layer_aggregator_seq006_v001.py` | 89 | 🔴 class | `EventAggregator` |
| `streaming_layer_metrics_seq007_v001.py` | 82 | 🔴 class | `MetricsCollector` |
| `streaming_layer_alerts_seq008_v001.py` | 122 | 🔴 class | `AlertEngine` |
| `streaming_layer_replay_seq009_v001.py` | 100 | 🔴 class | `SessionReplay` |
| `streaming_layer_dashboard_seq010_v001.py` | 72 | 🔴 class | `LiveDashboard` |
| `streaming_layer_http_handler_seq011_v001.py` | 127 | 🔴 class | `TelemetryHTTPHandler` |
| `streaming_layer_orchestrator_seq016_v001.py` | 121 | 🔴 class | `StreamingTelemetryServer` |
| `streaming_layer_orchestrator_seq017_v001.py` | 9 | ✅ | `run_demo` |
| `streaming_layer_demo_functions_seq013_v001.py` | 46 | ✅ | demo helpers |
| `streaming_layer_demo_functions_seq014_v001.py` | 27 | ✅ | demo helpers |
| `streaming_layer_demo_simulate_seq014_v001.py` | 23 | ✅ | `_run_demo_simulate_activity` |
| `streaming_layer_demo_summary_seq013_v001.py` | 34 | ✅ | `_run_demo_print_summary` |

✅ = ≤50 lines | 🔴 = single-class file (indivisible at AST level, expected)

### pigeon_compiler/ — The Compiler (30+ modules)

See `pigeon_compiler/MANIFEST.md` for detailed breakdown.

---

## 🧪 TEST STATUS

| Test | Description | Status |
|------|-------------|--------|
| TEST 1 | Telemetry Logger — v2 schema, 3 turns, submit + discard | ✅ PASS |
| TEST 2 | Context Budget Scorer — hard cap, budget, coupling | ✅ PASS |
| TEST 3 | Drift Watcher — baseline + drift detection | ✅ PASS |
| TEST 4 | Resistance Bridge — telemetry → compiler signal | ✅ PASS |

```bash
py test_all.py   # All 4 tests pass, zero dependencies
```

---

## 🔧 COMPILER BUG FIXES (v0.2.0)

Three bugs fixed in the pigeon compiler during this session:

1. **Indentation error in generated files** — `_collect_imports()` used `ast.walk()` which collected imports from inside function bodies (indented). Fixed: `ast.iter_child_nodes(tree)` in both `file_writer_seq003` and `resplit_helpers_seq011`.

2. **Classes extracted as empty stubs** — DeepSeek prompt had no `"classes"` key, runner ignored classes, `_scan_exports` skipped `ClassDef`. Fixed: added `"classes"` throughout the pipeline.

3. **Infinite resplit loop** — Single-class files (indivisible at AST level) triggered infinite re-split attempts. Fixed: `scan_violations()` skips single-class files, `bin_pack()` gives classes their own bin.

---

## 📦 PROMPT BOX — DEVELOPMENT PLAN

*Last updated: 2026-03-11*

### Phase 1 — Core Telemetry ✅ COMPLETE
- [x] **KT-001**: Timestamp utility (ms-epoch)
- [x] **KT-002**: KeyEvent + MessageDraft dataclasses
- [x] **KT-003**: Core telemetry logger with v2 schema
- [x] **KT-004**: Context budget scorer (token-aware)
- [x] **KT-005**: Drift watcher (live coding loop detection)
- [x] **KT-006**: Resistance bridge (telemetry → compiler signal)
- [x] **KT-007**: Streaming layer monolith (compiler test target)

### Phase 2 — Compiler Integration ✅ COMPLETE
- [x] **KT-008**: Run pigeon compiler on streaming_layer monolith
- [x] **KT-009**: Fix compiler bug — indentation errors in output
- [x] **KT-010**: Fix compiler bug — class extraction (empty stubs)
- [x] **KT-011**: Fix compiler bug — infinite resplit loop + manifest
- [x] **KT-012**: Verify all compiled output parses (19/19 clean)
- [x] **KT-013**: Run test_all.py — all 4 tests pass
- [x] **KT-014**: Run drift watcher on compiled output
- [x] **KT-015**: Commit pigeon compiler + compiled output

### Phase 3 — Streaming Layer Activation 🔲 NEXT
- [ ] **KT-016**: Fix compiled demo imports (reference correct module paths)
- [ ] **KT-017**: Run `streaming_layer.run_demo()` end-to-end
- [ ] **KT-018**: Verify HTTP endpoint serves SSE stream on localhost:8787
- [ ] **KT-019**: Test live dashboard rendering in terminal
- [ ] **KT-020**: Test session replay from JSONL files
- [ ] **KT-021**: Add streaming_layer tests to test_all.py

### Phase 4 — Operator Profiling 🔲 PLANNED
- [ ] **KT-022**: Persistent operator profile (cross-session state)
- [ ] **KT-023**: Profile fingerprinting (WPM, hesitation, discard patterns)
- [ ] **KT-024**: Confidence scoring (min 3 sessions for "medium")
- [ ] **KT-025**: Profile drift detection (operator behavior changes)
- [ ] **KT-026**: Profile export (JSON summary for LLM consumption)

### Phase 5 — Live Agent Integration 🔲 PLANNED
- [ ] **KT-027**: Real-time agent hook (stream events to LLM via SSE)
- [ ] **KT-028**: Agent-triggered split suggestions based on hesitation
- [ ] **KT-029**: Two-way: agent reads telemetry, emits recommendations
- [ ] **KT-030**: Resistance feedback loop (compiler re-runs on high-hesitation files)
- [ ] **KT-031**: Multi-session resistance accumulation

### Phase 6 — Packaging + Distribution 🔲 PLANNED
- [ ] **KT-032**: PyPI-ready packaging (setup.py / pyproject.toml)
- [ ] **KT-033**: CLI entry point: `keystroke-telemetry serve`
- [ ] **KT-034**: Documentation site (or comprehensive README expansion)
- [ ] **KT-035**: CI/CD pipeline (GitHub Actions)
- [ ] **KT-036**: Version tagging + release workflow

---

## CHANGELOG

### v0.2.0 (2026-03-11)
- **Added**: Pigeon compiler (embedded, bugfixed) — 30+ modules
- **Added**: `streaming_layer/` compiled output — 20 files from 956-line monolith
- **Fixed**: 3 compiler bugs (import collection, class extraction, resplit loop)
- **Added**: Subfolder MANIFEST.md with PROMPT BOX, STRUCTURE, CHANGELOG
- **Added**: `demo_logs/` sample telemetry session
- **Cost**: $0.0045 DeepSeek API (one compilation run)
- **Status**: All tests pass, 6 drift warnings (expected single-class files)

### v0.1.0 (2026-03-11)
- **Initial**: Core telemetry library — 6 modules, 468 lines
- **Schema**: `keystroke_telemetry/v2` — self-contained JSON blocks
- **Features**: Logger, context budget, drift watcher, resistance bridge
- **Tests**: 4 tests, all pass
- **Status**: All files pigeon-compliant (≤88 lines)
