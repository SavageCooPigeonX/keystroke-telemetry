# MASTER_MANIFEST.md — keystroke-telemetry
**Version**: v1.0.0 | **Last Updated**: 2026-03-15

---

## PROJECT OVERVIEW

Two developer tools packaged together:

1. **Keystroke Telemetry** — Browser-to-server pipeline that captures typing patterns in LLM chat interfaces, classifies operator cognitive state (7 states), reconstructs unsaid thoughts, and detects cross-session drift. Zero LLM calls — pure signal processing.

2. **Pigeon Code Compiler** — Autonomous code decomposition engine that enforces LLM-readable file sizes (≤50 lines), pigeon-code naming (`{name}_seq{NNN}_v{NNN}_d{MMDD}__{desc}_lc_{intent}.py`), and self-healing renames with rollback.

**Stack**: Python 3.13 Windows (`py` launcher) + httpx (compiler DeepSeek calls)
**Browser**: Vanilla JS, zero dependencies
**Schema**: `keystroke_telemetry/v2` — self-contained JSON blocks per event

---

## FOLDER TREE
*Auto-synced by manifest_builder | 2026-03-16 03:21 UTC*

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
+-- /pigeon_compiler                     46 files, 7 sub | 72% compliant
|   +-- /cut_executor                    (12 files)
|   +-- /integrations                    (1 files)
|   +-- /rename_engine                   (12 files)
|   +-- /runners                         (9 files)
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
+-- /test_logs                           (36 files)
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

### src/cognitive/ — Intelligence Layer (3 modules + 2 compiled packages)

| File | Lines | Role | Exports |
|------|-------|------|---------|
| `adapter_seq001_v*_d*__*.py` | 107 | State → prompt modifiers | `get_cognitive_modifier`, `VALID_STATES` |
| `unsaid_seq002_v*_d*__*.py` | 195 | Unsaid thought reconstruction | `extract_unsaid_thoughts` |
| `drift_seq003_v*_d*__*.py` | 215 | Cross-session drift detection | `BaselineStore`, `compute_baseline`, `detect_session_drift`, `build_cognitive_context` |

Compiled packages: `unsaid/` (9 files), `drift/` (7 files).

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
py test_all.py   # All 4 tests pass, zero dependencies
```

---

## OPERATOR KEYSTROKE TRAIL

*Last 50 keystrokes | auto-synced by manifest_builder | 2026-03-16 03:21 UTC*

> **How to read**: Each row is one keystroke event from the operator.
> Markers flag cognitive signals: ⏸ = long pause (>2s), 
> ⌫ = backspace burst (3+), ✓ = submitted, 🗑 = discarded.
> Hesitation scores come from session summaries (0.0 = confident, 1.0 = max hesitation).

| # | Key | Event | Δms | Buffer | Markers |
|---|-----|-------|----:|--------|---------|
| 1 | `What is the meaning of life?` | paste | 0 | `What is the meaning of life?` |  |
| 2 | `?` | backspace | 0 | `What is the meaning of life` | ⌫ burst |
| 3 | `e` | backspace | 41 | `What is the meaning of lif` | ⌫ burst |
| 4 | `f` | backspace | 41 | `What is the meaning of li` | ⌫ burst |
| 5 | `i` | backspace | 40 | `What is the meaning of l` | ⌫ burst |
| 6 | `l` | backspace | 41 | `What is the meaning of ` | ⌫ burst |
| 7 | `4` | insert | 41 | `What is the meaning of 4` |  |
| 8 | `2` | insert | 150 | `What is the meaning of 42` |  |
| 9 | `?` | insert | 151 | `What is the meaning of 42?` |  |
| 10 | `H` | insert | 0 | `H` |  |
| 11 | `e` | insert | 153 | `He` |  |
| 12 | `l` | insert | 151 | `Hel` |  |
| 13 | `o` | insert | 152 | `Helo` |  |
| 14 | ` ` | insert | 151 | `Helo ` |  |
| 15 | `w` | insert | 150 | `Helo w` |  |
| 16 | `r` | insert | 153 | `Helo wr` |  |
| 17 | `l` | insert | 150 | `Helo wrl` |  |
| 18 | `d` | insert | 154 | `Helo wrld` |  |
| 19 | `d` | backspace | 153 | `Helo wrl` | ⌫ burst |
| 20 | `l` | backspace | 41 | `Helo wr` | ⌫ burst |
| 21 | `r` | backspace | 40 | `Helo w` | ⌫ burst |
| 22 | `w` | backspace | 42 | `Helo ` | ⌫ burst |
| 23 | `w` | insert | 42 | `Helo w` |  |
| 24 | `o` | insert | 150 | `Helo wo` |  |
| 25 | `r` | insert | 152 | `Helo wor` |  |
| 26 | `l` | insert | 151 | `Helo worl` |  |
| 27 | `d` | insert | 151 | `Helo world` |  |
| 28 | `!` | insert | 151 | `Helo world!` |  |
| 29 | `A` | insert | 0 | `A` |  |
| 30 | `c` | insert | 167 | `Ac` |  |
| 31 | `t` | insert | 168 | `Act` |  |
| 32 | `u` | insert | 187 | `Actu` |  |
| 33 | `a` | insert | 163 | `Actua` |  |
| 34 | `l` | insert | 166 | `Actual` |  |
| 35 | `l` | insert | 152 | `Actuall` |  |
| 36 | `y` | insert | 169 | `Actually` |  |
| 37 | ` ` | insert | 152 | `Actually ` |  |
| 38 | `n` | insert | 150 | `Actually n` |  |
| 39 | `v` | insert | 157 | `Actually nv` |  |
| 40 | `m` | insert | 154 | `Actually nvm` |  |
| 41 | `Ctrl+A+Del` | clear | 2304 | `` | ⏸ 2.3s |
| 42 | `What is the meaning of life?` | paste | 0 | `What is the meaning of life?` |  |
| 43 | `?` | backspace | 1 | `What is the meaning of life` | ⌫ burst |
| 44 | `e` | backspace | 84 | `What is the meaning of lif` | ⌫ burst |
| 45 | `f` | backspace | 130 | `What is the meaning of li` | ⌫ burst |
| 46 | `i` | backspace | 88 | `What is the meaning of l` | ⌫ burst |
| 47 | `l` | backspace | 64 | `What is the meaning of ` | ⌫ burst |
| 48 | `4` | insert | 85 | `What is the meaning of 4` |  |
| 49 | `2` | insert | 161 | `What is the meaning of 42` |  |
| 50 | `?` | insert | 153 | `What is the meaning of 42?` |  |

### Recent message hesitation scores

| Message | Submitted | Keys | Dels | Hesitation | State |
|---------|-----------|-----:|-----:|-----------:|-------|
| `64af8164d2` | ✓ | 19 | 4 | 0.211 | restructuring |
| `4f1dceb3be` | 🗑 | 13 | 0 | 0.563 | abandoned |
| `61b721b85a` | ✓ | 9 | 5 | 0.556 | hesitant |
| `0608eeb2ba` | ✓ | 19 | 4 | 0.211 | restructuring |
| `816b724b8c` | 🗑 | 13 | 0 | 0.575 | abandoned |
| `b8965a20c5` | ✓ | 9 | 5 | 0.556 | hesitant |
| `093b44e6df` | ✓ | 19 | 4 | 0.211 | restructuring |
| `eac9de2d90` | 🗑 | 13 | 0 | 0.575 | abandoned |
| `e6b7a4bad2` | ✓ | 9 | 5 | 0.556 | hesitant |
| `b4542e8aa0` | ✓ | 19 | 4 | 0.211 | restructuring |
| `206e4ec333` | 🗑 | 13 | 0 | 0.576 | abandoned |
| `f13a376a02` | ✓ | 9 | 5 | 0.556 | hesitant |


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
