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
*Auto-synced by manifest_builder | 2026-03-16 00:08 UTC*

```
LinkRouter.AI/
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
+-- /pigeon_compiler                     44 files, 7 sub | 73% compliant
|   +-- /cut_executor                    (11 files)
|   +-- /integrations                    (1 files)
|   +-- /rename_engine                   (12 files)
|   +-- /runners                         (8 files)
|   +-- /state_extractor                 (6 files)
|   +-- /weakness_planner                (1 files)
|
+-- /src                                 11 files, 1 sub | 64% compliant
|   +-- /cognitive                       (3 files)
|
+-- /streaming_layer                     19 files | 100% compliant
|
+-- /stress_logs                         (2 files)
+-- /test_logs                           (22 files)
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

*Last 50 keystrokes | auto-synced by manifest_builder | 2026-03-16 00:08 UTC*

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
| 7 | `4` | insert | 40 | `What is the meaning of 4` |  |
| 8 | `2` | insert | 151 | `What is the meaning of 42` |  |
| 9 | `?` | insert | 150 | `What is the meaning of 42?` |  |
| 10 | `H` | insert | 0 | `H` |  |
| 11 | `e` | insert | 151 | `He` |  |
| 12 | `l` | insert | 160 | `Hel` |  |
| 13 | `o` | insert | 156 | `Helo` |  |
| 14 | ` ` | insert | 151 | `Helo ` |  |
| 15 | `w` | insert | 151 | `Helo w` |  |
| 16 | `r` | insert | 151 | `Helo wr` |  |
| 17 | `l` | insert | 162 | `Helo wrl` |  |
| 18 | `d` | insert | 165 | `Helo wrld` |  |
| 19 | `d` | backspace | 168 | `Helo wrl` | ⌫ burst |
| 20 | `l` | backspace | 45 | `Helo wr` | ⌫ burst |
| 21 | `r` | backspace | 100 | `Helo w` | ⌫ burst |
| 22 | `w` | backspace | 41 | `Helo ` | ⌫ burst |
| 23 | `w` | insert | 69 | `Helo w` |  |
| 24 | `o` | insert | 196 | `Helo wo` |  |
| 25 | `r` | insert | 150 | `Helo wor` |  |
| 26 | `l` | insert | 152 | `Helo worl` |  |
| 27 | `d` | insert | 151 | `Helo world` |  |
| 28 | `!` | insert | 151 | `Helo world!` |  |
| 29 | `A` | insert | 0 | `A` |  |
| 30 | `c` | insert | 151 | `Ac` |  |
| 31 | `t` | insert | 150 | `Act` |  |
| 32 | `u` | insert | 151 | `Actu` |  |
| 33 | `a` | insert | 194 | `Actua` |  |
| 34 | `l` | insert | 160 | `Actual` |  |
| 35 | `l` | insert | 151 | `Actuall` |  |
| 36 | `y` | insert | 152 | `Actually` |  |
| 37 | ` ` | insert | 150 | `Actually ` |  |
| 38 | `n` | insert | 154 | `Actually n` |  |
| 39 | `v` | insert | 155 | `Actually nv` |  |
| 40 | `m` | insert | 150 | `Actually nvm` |  |
| 41 | `Ctrl+A+Del` | clear | 2251 | `` | ⏸ 2.3s |
| 42 | `What is the meaning of life?` | paste | 0 | `What is the meaning of life?` |  |
| 43 | `?` | backspace | 0 | `What is the meaning of life` | ⌫ burst |
| 44 | `e` | backspace | 41 | `What is the meaning of lif` | ⌫ burst |
| 45 | `f` | backspace | 40 | `What is the meaning of li` | ⌫ burst |
| 46 | `i` | backspace | 42 | `What is the meaning of l` | ⌫ burst |
| 47 | `l` | backspace | 43 | `What is the meaning of ` | ⌫ burst |
| 48 | `4` | insert | 41 | `What is the meaning of 4` |  |
| 49 | `2` | insert | 151 | `What is the meaning of 42` |  |
| 50 | `?` | insert | 150 | `What is the meaning of 42?` |  |

### Recent message hesitation scores

| Message | Submitted | Keys | Dels | Hesitation | State |
|---------|-----------|-----:|-----:|-----------:|-------|
| `146728f7a9` | ✓ | 19 | 4 | 0.211 | restructuring |
| `55787b7c2c` | 🗑 | 13 | 0 | 0.567 | abandoned |
| `4602f5b4a9` | ✓ | 9 | 5 | 0.556 | hesitant |
| `9492f51b2c` | ✓ | 19 | 4 | 0.211 | restructuring |
| `ddaa7375e0` | 🗑 | 13 | 0 | 0.576 | abandoned |
| `5f836dd9dd` | ✓ | 9 | 5 | 0.556 | hesitant |
| `5c6b75f699` | ✓ | 19 | 4 | 0.211 | restructuring |
| `c05a288bdd` | 🗑 | 13 | 0 | 0.576 | abandoned |
| `66bd161695` | ✓ | 9 | 5 | 0.556 | hesitant |
| `b8ee15abb2` | ✓ | 19 | 4 | 0.211 | restructuring |
| `045e28823a` | 🗑 | 13 | 0 | 0.576 | abandoned |
| `d477f482ce` | ✓ | 9 | 5 | 0.556 | hesitant |


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
