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
*Auto-synced by manifest_builder | 2026-03-16 02:24 UTC*

```
LinkRouter.AI/
+-- _test_import_rewriter_patch.py
+-- MANIFEST.md
+-- MASTER_MANIFEST.md
+-- operator_profile.md
+-- pigeon_registry.json
+-- pyproject.toml
+-- README.md
+-- stress_test.py
+-- test_all.py
+-- test_public_release.py
|
+-- /client                              (1 files)
+-- /demo_logs                           (2 files)
+-- /documentation                       (1 files)
+-- /pigeon_code.egg-info                (5 files)
+-- /pigeon_compiler                     59 files, 9 sub | 75% compliant
|   +-- /bones                           (5 files)
|   +-- /cut_executor                    (12 files)
|   +-- /integrations                    (1 files)
|   +-- /rename_engine                   (12 files)
|   +-- /runners                         (17 files)
|   +-- /state_extractor                 (6 files)
|   +-- /weakness_planner                (1 files)
|
+-- /src                                 38 files, 2 sub | 89% compliant
|   +-- /cognitive                       (17 files)
|   +-- /operator_stats                  (13 files)
|
+-- /streaming_layer                     19 files | 100% compliant
|
+-- /stress_logs                         (2 files)
```

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

## OPERATOR KEYSTROKE TRAIL

*Last 50 keystrokes | auto-synced by manifest_builder | 2026-03-16 02:24 UTC*

> **How to read**: Each row is one keystroke event from the operator.
> Markers flag cognitive signals: ⏸ = long pause (>2s), 
> ⌫ = backspace burst (3+), ✓ = submitted, 🗑 = discarded.
> Hesitation scores come from session summaries (0.0 = confident, 1.0 = max hesitation).

| # | Key | Event | Δms | Buffer | Markers |
|---|-----|-------|----:|--------|---------|
| 1 | `o` | insert | 47 | `Stream events into ring buf...` |  |
| 2 | `n` | insert | 44 | `Stream events into ring buf...` |  |
| 3 | ` ` | insert | 45 | `Stream events into ring buf...` |  |
| 4 | `t` | insert | 32 | `Stream events into ring buf...` |  |
| 5 | `h` | insert | 32 | `Stream events into ring buf...` |  |
| 6 | `r` | insert | 42 | `Stream events into ring buf...` |  |
| 7 | `e` | insert | 26 | `Stream events into ring buf...` |  |
| 8 | `s` | insert | 34 | `Stream events into ring buf...` |  |
| 9 | `h` | insert | 28 | `Stream events into ring buf...` |  |
| 10 | `o` | insert | 40 | `Stream events into ring buf...` |  |
| 11 | `l` | insert | 43 | `Stream events into ring buf...` |  |
| 12 | `d` | insert | 27 | `Stream events into ring buf...` |  |
| 13 | `,` | insert | 46 | `Stream events into ring buf...` |  |
| 14 | ` ` | insert | 22 | `Stream events into ring buf...` |  |
| 15 | `a` | insert | 29 | `Stream events into ring buf...` |  |
| 16 | `g` | insert | 50 | `Stream events into ring buf...` |  |
| 17 | `g` | insert | 44 | `Stream events into ring buf...` |  |
| 18 | `r` | insert | 48 | `Stream events into ring buf...` |  |
| 19 | `e` | insert | 27 | `Stream events into ring buf...` |  |
| 20 | `g` | insert | 47 | `Stream events into ring buf...` |  |
| 21 | `a` | insert | 29 | `Stream events into ring buf...` |  |
| 22 | `t` | insert | 32 | `Stream events into ring buf...` |  |
| 23 | `e` | insert | 33 | `Stream events into ring buf...` |  |
| 24 | ` ` | insert | 39 | `Stream events into ring buf...` |  |
| 25 | `p` | insert | 39 | `Stream events into ring buf...` |  |
| 26 | `e` | insert | 31 | `Stream events into ring buf...` |  |
| 27 | `r` | insert | 47 | `Stream events into ring buf...` |  |
| 28 | ` ` | insert | 40 | `Stream events into ring buf...` |  |
| 29 | `w` | insert | 45 | `Stream events into ring buf...` |  |
| 30 | `i` | insert | 26 | `Stream events into ring buf...` |  |
| 31 | `n` | insert | 33 | `Stream events into ring buf...` |  |
| 32 | `d` | insert | 28 | `Stream events into ring buf...` |  |
| 33 | `o` | insert | 48 | `Stream events into ring buf...` |  |
| 34 | `q` | insert | 51 | `Stream events into ring buf...` |  |
| 35 | `Backspace` | backspace | 27 | `Stream events into ring buf...` |  |
| 36 | `w` | insert | 26 | `Stream events into ring buf...` |  |
| 37 | `,` | insert | 35 | `Stream events into ring buf...` |  |
| 38 | ` ` | insert | 82 | `Stream events into ring buf...` |  |
| 39 | `e` | insert | 55 | `Stream events into ring buf...` |  |
| 40 | `m` | insert | 27 | `Stream events into ring buf...` |  |
| 41 | `i` | insert | 34 | `Stream events into ring buf...` |  |
| 42 | `t` | insert | 35 | `Stream events into ring buf...` |  |
| 43 | ` ` | insert | 38 | `Stream events into ring buf...` |  |
| 44 | `m` | insert | 41 | `Stream events into ring buf...` |  |
| 45 | `e` | insert | 30 | `Stream events into ring buf...` |  |
| 46 | `t` | insert | 51 | `Stream events into ring buf...` |  |
| 47 | `r` | insert | 42 | `Stream events into ring buf...` |  |
| 48 | `i` | insert | 41 | `Stream events into ring buf...` |  |
| 49 | `c` | insert | 36 | `Stream events into ring buf...` |  |
| 50 | `s` | insert | 38 | `Stream events into ring buf...` |  |

### Recent message hesitation scores

| Message | Submitted | Keys | Dels | Hesitation | State |
|---------|-----------|-----:|-----:|-----------:|-------|
| `8f857c219f` | ✓ | 50 | 0 | 0.000 | flow |
| `3809d68036` | ✓ | 58 | 12 | 0.207 | restructuring |
| `a8a773a867` | 🗑 | 36 | 0 | 0.000 | abandoned |
| `bb736b0189` | ✓ | 73 | 1 | 0.014 | flow |
| `3bd1f0afe1` | ✓ | 73 | 3 | 0.740 | frustrated |
| `c5859e900e` | ✓ | 73 | 35 | 1.000 | frustrated |
| `91a3db4af5` | 🗑 | 82 | 26 | 1.000 | abandoned |
| `3533cb51c3` | ✓ | 88 | 1 | 0.011 | flow |


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
