# MASTER_MANIFEST.md — keystroke-telemetry
**Version**: v1.0.0 | **Last Updated**: 2026-03-15

---

## PROJECT OVERVIEW

Two developer tools packaged together:

1. **Keystroke Telemetry** — Browser-to-server pipeline that captures typing patterns in LLM chat interfaces, classifies operator cognitive state (7 states), reconstructs unsaid thoughts, and detects cross-session drift. Zero LLM calls — pure signal processing.

2. **Pigeon Code Compiler** — Autonomous code decomposition engine that enforces LLM-readable file sizes (≤50 lines), pigeon-code naming (`{name}_seq{NNN}_v{NNN}_d{MMDD}__{desc}_lc_{intent}.py`), and self-healing renames with rollback.

**Stack**: Python 3.10+ stdlib (core) + httpx (compiler DeepSeek calls)
**Browser**: Vanilla JS, zero dependencies
**Schema**: `keystroke_telemetry/v2` — self-contained JSON blocks per event

---

## FOLDER TREE

```
keystroke-telemetry/
│
├── client/                                        # Browser capture layer (JavaScript)
│   └── keystroke-telemetry.js                     #   IIFE: attach/onSubmit/getLastState (210 lines)
│
├── src/                                           # Core telemetry library (Python)
│   ├── __init__.py                                #   Package root — all exports
│   ├── timestamp_utils_seq001_v*_d*__*.py         #   ms-epoch utility
│   ├── models_seq002_v*_d*__*.py                  #   KeyEvent + MessageDraft dataclasses
│   ├── logger_seq003_v*_d*__*.py                  #   Core logger, v2 schema
│   ├── context_budget_seq004_v*_d*__*.py          #   LLM-aware file sizing scorer
│   ├── drift_watcher_seq005_v*_d*__*.py           #   Live drift detection for coding loops
│   ├── resistance_bridge_seq006_v*_d*__*.py       #   Telemetry → compiler resistance signal
│   ├── streaming_layer_seq007_v*_d*__*.py         #   Compiler test input monolith
│   ├── operator_stats_seq008_v*_d*__*.py          #   Self-growing operator profile
│   │
│   └── cognitive/                                 #   Cognitive intelligence layer
│       ├── __init__.py                            #     Package root: re-exports all cognitive APIs
│       ├── adapter_seq001_v*_d*__*.py             #     7 states → prompt injection + temp modifiers
│       ├── unsaid_seq002_v*_d*__*.py              #     Reconstruct deleted/abandoned text
│       └── drift_seq003_v*_d*__*.py               #     Cross-session drift + baseline store
│
├── streaming_layer/                               # Pigeon-compiled output from seq007
│   ├── __init__.py                                #   Re-exports all public names
│   ├── streaming_layer_*_v*_d*__*.py              #   20 extracted modules
│   └── MANIFEST.md                                #   Subfolder manifest + prompt box
│
├── pigeon_compiler/                               # Autonomous code decomposition engine
│   ├── state_extractor/                           #   Layer 1: AST parsing, call graphs, resistance
│   │   ├── ast_parser_seq001_v003.py              #     Parse → functions, classes, constants
│   │   ├── call_graph_seq002_v003.py              #     Intra-file call graph
│   │   ├── import_tracer_seq003_v003.py           #     Outbound + inbound imports
│   │   ├── shared_state_detector_seq004_v003.py   #     Module-level state detection
│   │   ├── resistance_analyzer_seq005_v003.py     #     Coupling + resistance scoring
│   │   └── ether_map_builder_seq006_v003.py       #     Orchestrate → full ether map JSON
│   │
│   ├── weakness_planner/                          #   Layer 2: DeepSeek cut planning
│   │   └── deepseek_plan_prompt_seq004_v003.py    #     Build prompt, send, validate plan
│   │
│   ├── cut_executor/                              #   Layer 3: Deterministic execution
│   │   ├── plan_parser_seq001_v003.py             #     Parse DeepSeek JSON response
│   │   ├── source_slicer_seq002_v003.py           #     Extract funcs/classes by name
│   │   ├── file_writer_seq003_v003.py             #     Write pigeon-compliant files
│   │   ├── import_fixer_seq004_v003.py            #     Resolve imports per file
│   │   ├── manifest_writer_seq005_v003.py         #     Generate subfolder MANIFEST.md
│   │   ├── plan_validator_seq006_v003.py          #     Validate plan before execution
│   │   ├── init_writer_seq007_v003.py             #     Generate __init__.py re-exports
│   │   ├── func_decomposer_seq008_v003.py         #     Decompose oversized functions
│   │   ├── resplit_seq009_v003.py                 #     Deterministic AST re-splitter
│   │   ├── resplit_binpack_seq010_v003.py         #     First-fit-decreasing bin packer
│   │   └── resplit_helpers_seq011_v003.py         #     Shared resplit utilities
│   │
│   ├── rename_engine/                             #   Autonomous renames with rollback
│   │   ├── scanner_seq001_v003.py                 #     Walk project tree, find non-compliant
│   │   ├── planner_seq002_v003.py                 #     Generate rename plan
│   │   ├── import_rewriter_seq003_v003.py         #     Rewrite all imports project-wide
│   │   ├── executor_seq004_v003.py                #     Apply renames with atomic rollback
│   │   ├── validator_seq005_v003.py               #     Post-rename import validation
│   │   ├── run_rename_seq006_v003.py              #     Full rename pipeline runner
│   │   ├── manifest_builder_seq007_v003.py        #     Generate living MANIFEST.md
│   │   ├── compliance_seq008_v003.py              #     Line count enforcer + split recommender
│   │   ├── heal_seq009_v003.py                    #     Self-healing orchestrator
│   │   ├── run_heal_seq010_v003.py                #     Automated self-healing pipeline
│   │   ├── nametag_seq011_v003.py                 #     Encode description + intent into name
│   │   └── registry_seq012_v003.py                #     Local name registry
│   │
│   ├── runners/                                   #   Pipeline orchestrators
│   │   ├── run_compiler_test_seq007_v003.py       #     Self-test compiler on own code
│   │   ├── run_deepseek_plans_seq008_v003.py      #     Phase 2: send ether maps to DeepSeek
│   │   ├── run_pigeon_loop_seq009_v003.py         #     Refactor until pigeon-compliant
│   │   ├── run_clean_split_seq010_v003.py         #     Full 6-phase pipeline
│   │   ├── run_clean_split_helpers_seq011_v003.py #     Phase 1 decomposition helpers
│   │   ├── run_clean_split_init_seq012_v003.py    #     Phase 5 init + manifest writers
│   │   ├── manifest_bridge_seq013_v003.py         #     Phase 6 master manifest update
│   │   └── reaudit_diff_seq014_v003.py            #     Re-audit with diff across versions
│   │
│   ├── integrations/
│   │   └── deepseek_adapter_seq001_v003.py        #     DeepSeek API with retry + timeout
│   │
│   ├── bones/                                     #   Shared utilities (5 modules)
│   ├── docs/                                      #   Design documentation (5 docs)
│   └── pigeon_limits.py                           #   PIGEON_MAX=50, PIGEON_HARD=88
│
├── test_all.py                                    # Full test suite
├── stress_test.py                                 # Cognitive stress test (5 scenarios)
├── operator_profile.md                            # Auto-generated operator stats
├── demo_logs/                                     # Demo session artifacts
├── stress_logs/                                   # Stress test artifacts
└── README.md                                      # Project readme
```

---

## MODULE INVENTORY

### client/ — Browser Capture (1 file, ~210 lines)

| File | Role | API |
|------|------|-----|
| `keystroke-telemetry.js` | IIFE browser capture | `attach()`, `onSubmit()`, `getLastState()`, `setEntityId()` |

Schema: `keystroke_telemetry/v2`. Auto-flush at 200 events. Abandon detection (30s blur timeout). Paste tracking. Cognitive pause detection (>2s gaps).

### src/ — Core Telemetry (8 modules + cognitive/)

| File | Lines | Role | Exports |
|------|-------|------|---------|
| `timestamp_utils_seq001_v*_d*__*.py` | 8 | Utility | `_now_ms` |
| `models_seq002_v*_d*__*.py` | 39 | Data models | `KeyEvent`, `MessageDraft` |
| `logger_seq003_v*_d*__*.py` | 158 | Core logger | `TelemetryLogger`, `SCHEMA_VERSION` |
| `context_budget_seq004_v*_d*__*.py` | 80 | Budget scorer | `score_context_budget`, `estimate_tokens` |
| `drift_watcher_seq005_v*_d*__*.py` | 103 | Drift detection | `DriftWatcher` |
| `resistance_bridge_seq006_v*_d*__*.py` | 119 | Compiler bridge | `HesitationAnalyzer` |
| `streaming_layer_seq007_v*_d*__*.py` | 1150 | Monolith (test) | 8 classes, ~15 functions |
| `operator_stats_seq008_v*_d*__*.py` | 394 | Self-growing profile | `OperatorStats` |

### src/cognitive/ — Intelligence Layer (3 modules)

| File | Lines | Role | Exports |
|------|-------|------|---------|
| `adapter_seq001_v*_d*__*.py` | 107 | State → prompt modifiers | `get_cognitive_modifier`, `VALID_STATES` |
| `unsaid_seq002_v*_d*__*.py` | 195 | Unsaid thought reconstruction | `extract_unsaid_thoughts` |
| `drift_seq003_v*_d*__*.py` | 215 | Cross-session drift detection | `BaselineStore`, `compute_baseline`, `detect_session_drift`, `build_cognitive_context` |

Seven cognitive states: `frustrated`, `hesitant`, `flow`, `focused`, `restructuring`, `abandoned`, `neutral`.

### pigeon_compiler/ — Decomposition Engine (~62 modules, v003)

| Subpackage | Files | Role |
|------------|-------|------|
| `state_extractor/` | 6 | AST parsing, call graphs, import tracing, resistance scoring |
| `weakness_planner/` | 1 | DeepSeek-powered cut plan generation |
| `cut_executor/` | 11 | File slicing, writing, bin-packing, resplit |
| `rename_engine/` | 12 | Autonomous renames, rollback, self-healing |
| `runners/` | 8 | Pipeline orchestrators |
| `integrations/` | 1 | DeepSeek API adapter |
| `bones/` | 5 | Shared utilities |
| `docs/` | 5 | Design documentation |

---

## TEST STATUS

| Test | Description | Status |
|------|-------------|--------|
| TEST 1 | Telemetry Logger — v2 schema, 3 turns, submit + discard | PASS |
| TEST 2 | Context Budget Scorer — hard cap, budget, coupling | PASS |
| TEST 3 | Drift Watcher — baseline + versioned filename drift detection | PASS |
| TEST 4 | Resistance Bridge — telemetry → compiler signal | PASS |

```bash
python test_all.py   # All 4 tests pass, zero dependencies
```

---

## CHANGELOG

### v1.0.0 (2026-03-15)
- **Added**: Cognitive intelligence layer — 3 modules (adapter, unsaid, drift)
- **Added**: Browser capture client (`client/keystroke-telemetry.js`)
- **Added**: Rename engine — 12 modules with rollback + self-healing
- **Upgraded**: Pigeon compiler to v003 (all 62 modules renamed)
- **Added**: Self-growing operator profile
- **Packaging**: Two-business-line structure (telemetry + compiler)

### v0.2.0 (2026-03-11)
- **Added**: Pigeon compiler (embedded, bugfixed) — 30+ modules
- **Added**: `streaming_layer/` compiled output — 20 files from 956-line monolith
- **Fixed**: 3 compiler bugs (import collection, class extraction, resplit loop)

### v0.1.0 (2026-03-11)
- **Initial**: Core telemetry library — 6 modules, 468 lines
- **Schema**: `keystroke_telemetry/v2`
- **Features**: Logger, context budget, drift watcher, resistance bridge
