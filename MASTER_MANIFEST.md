# MASTER_MANIFEST.md — keystroke-telemetry
**Version**: v2.0.0 | **Last Updated**: 2026-03-16

```
# ── pigeon ────────────────────────────────────
# PROJECT: keystroke-telemetry
# MODULES: 85+ tracked | 19 compiled packages
# LINES:   ~12,000 across all modules
# SCHEMA:  keystroke_telemetry/v2
# DEEP:    rework_log + query_memory + file_heat_map
# REPO:    github.com/SavageCooPigeonX/keystroke-telemetry
# STATUS:  All systems live — deep profiling active
# LAST:    2026-03-16 @ a1eddf1
# ──────────────────────────────────────────────
```

---

## PROJECT OVERVIEW

Two developer tools packaged together:

1. **Keystroke Telemetry** — Browser-to-server pipeline that captures typing patterns in LLM chat interfaces, classifies operator cognitive state (7 states), reconstructs unsaid thoughts, detects cross-session drift, scores AI answer quality from post-response behavior, fingerprints recurring question gaps, and maps cognitive load per pigeon module. Zero LLM calls for classification — pure signal processing.

2. **Pigeon Code Compiler** — Autonomous code decomposition engine that enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target), pigeon-code naming (`{name}_seq{NNN}_v{NNN}_d{MMDD}__{desc}_lc_{intent}.py`), self-healing renames with rollback, and DeepSeek-powered coaching synthesis from deep telemetry signals.

**Stack**: Python 3.13 Windows (`py` launcher) + httpx (compiler DeepSeek calls) + TypeScript (VS Code extension)
**Browser**: Vanilla JS, zero dependencies
**Extension**: VS Code Pigeon Chat — full keystroke capture with post-response tracking
**Schema**: `keystroke_telemetry/v2` — self-contained JSON blocks per event

---

## FOLDER TREE
*Auto-synced by manifest_builder | 2026-03-22 19:40 UTC*

```
LinkRouter.AI/
+-- _audit_compliance.py
+-- CHANGELOG.md
+-- deep_test.py
+-- file_heat_map.json
+-- file_profiles.json
+-- MANIFEST.md
+-- MASTER_MANIFEST.md
+-- operator_coaching.md
+-- operator_profile.md
+-- pigeon_registry.json
+-- pyproject.toml
+-- query_memory.json
+-- README.md
+-- rework_log.json
+-- stress_test.py
+-- task_queue.json
+-- test_all.py
+-- test_public_release.py
|
+-- /client                              7 files, 1 sub | 14% compliant
|
+-- /demo_logs                           (2 files)
+-- /docs                                (51 files)
+-- /pigeon_code.egg-info                (5 files)
+-- /pigeon_compiler                     110 files, 7 sub | 88% compliant
|   +-- /cut_executor                    (12 files)
|   +-- /integrations                    (1 files)
|   +-- /rename_engine                   (76 files)
|   +-- /runners                         (9 files)
|   +-- /state_extractor                 (6 files)
|   +-- /weakness_planner                (1 files)
|
+-- /src                                 115 files, 7 sub | 87% compliant
|   +-- /cognitive                       (24 files)
|   +-- /cognitive_reactor_seq014        (12 files)
|   +-- /copilot_prompt_manager_seq020   (15 files)
|   +-- /dynamic_prompt_seq017           (15 files)
|   +-- /operator_stats                  (13 files)
|   +-- /operator_stats_seq008           (9 files)
|
+-- /streaming_layer                     19 files | 100% compliant
|
+-- /stress_logs                         (2 files)
+-- /test_logs                           (171 files)
+-- /vscode-extension                    2 files, 3 sub | 50% compliant
|
```

## MODULE INVENTORY

### client/ — Browser Capture (1 file, ~210 lines)

| File | Role | API |
|------|------|-----|
| `keystroke-telemetry.js` | IIFE browser capture | `attach()`, `onSubmit()`, `getLastState()`, `setEntityId()` |

Schema: `keystroke_telemetry/v2`. Auto-flush at 200 events. Abandon detection (30s blur timeout). Paste tracking. Cognitive pause detection (>2s gaps).

### src/ — Core Telemetry (11 modules + cognitive/)

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
| `rework_detector_seq009_v*_d*__*.py` | 106 | AI miss scoring | `score_rework`, `record_rework`, `load_rework_stats` |
| `query_memory_seq010_v*_d*__*.py` | 118 | Recurring gap fingerprinting | `record_query`, `load_query_memory` |
| `file_heat_map_seq011_v*_d*__*.py` | 139 | Cognitive load per module | `update_heat_map`, `load_heat_map` |

### src/cognitive/ — Intelligence Layer (3 modules + 2 compiled packages)

| File | Lines | Role | Exports |
|------|-------|------|---------|
| `adapter_seq001_v*_d*__*.py` | 107 | State → prompt modifiers | `get_cognitive_modifier`, `VALID_STATES` |
| `unsaid_seq002_v*_d*__*.py` | 195 | Unsaid thought reconstruction | `extract_unsaid_thoughts` |
| `drift_seq003_v*_d*__*.py` | 215 | Cross-session drift detection | `BaselineStore`, `compute_baseline`, `detect_session_drift`, `build_cognitive_context` |

Compiled packages: `unsaid/` (9 files), `drift/` (7 files).

Seven cognitive states: `frustrated`, `hesitant`, `flow`, `focused`, `restructuring`, `abandoned`, `neutral`.

Each state maps to a specific prompt injection + temperature modifier via `get_cognitive_modifier(state)`:

| State | Detection Signal | Temperature Δ | Prompt Strategy |
|---|---|---|---|
| `frustrated` | Heavy deletions + long pauses + high hesitation | −0.1 | Concise, 2-3 options, bullets |
| `hesitant` | Long inter-key pauses, low WPM | +0.05 | Warm, anticipate intent, follow-up question |
| `flow` | Fast typing, minimal edits | +0.1 | Match energy, technical depth, no hand-holding |
| `focused` | Steady, deliberate, engaged | 0 | Thorough, well-structured |
| `restructuring` | Heavy rewrite before submit | −0.05 | Precise, headers/numbered, match effort |
| `abandoned` | Deleted entire message, re-approached | 0 | Welcoming, direct |
| `neutral` | No strong signal | 0 | Standard |

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

## DEEP PROFILING SYSTEM

Three modules that run on every message in `classify_bridge.py`, building persistent JSON stores that feed into DeepSeek coaching synthesis.

### Rework Detector (`rework_detector_seq009*`)

Scores AI answer quality by observing operator behavior in the **30 seconds after receiving a response**. If heavy rework is detected (deletion-heavy retyping), the answer is classified as a "miss."

| Constant | Value | Purpose |
|---|---|---|
| `REWORK_WINDOW_MS` | 30,000 | Post-response capture window |
| `HEAVY_DEL_RATIO` | 0.35 | Deletion rate threshold for rework signal |
| Miss trigger | `score > 0.55 OR del_ratio > 0.35` | Classifies as "miss" |

**Key formula**: `del_ratio = len(deletes) / max(len(inserts) + len(deletes), 1)` — only actual keystrokes, not pause events. This prevents thinking pauses from diluting the deletion signal (bug fixed in v003).

**Verdicts**: `miss` (heavy rework) → `partial` (moderate) → `ok` (minimal rework)

**Store**: `rework_log.json` — plain JSON array:
```json
[{"ts": 1710561234, "verdict": "miss", "rework_score": 0.573, "del_ratio": 0.818, "wpm": 42.3, "query_hint": "how do I verify deepseek"}]
```

**Coaching feed**: `load_rework_stats()` → `{miss_rate, miss_count, total_responses, worst_queries}`

### Query Memory (`query_memory_seq010*`)

Fingerprints every query. When the same semantic question appears 3+ times, it's flagged as a **persistent gap** — a topic the AI consistently fails to resolve.

| Constant | Value | Purpose |
|---|---|---|
| `RECUR_THRESH` | 3 | Same fingerprint N times = persistent gap |
| `MAX_ENTRIES` | 500 | Circular buffer, oldest evicted |

**Fingerprinting**: `_fingerprint(text)` → lowercase, strip filler words, take 8 words, sort alphabetically. Order-invariant — "how do I verify deepseek" and "verify deepseek integration how" match.

**Store**: `query_memory.json`:
```json
{
  "queries": [{"ts": 1710561234, "text": "how do I verify deepseek", "fingerprint": "deepseek integration verify", "submitted": true}],
  "abandoned_themes": [{"ts": 1710561100, "text": "I already tried that", "state": "frustrated"}]
}
```

**Coaching feed**: `load_query_memory()` → `{total_queries, unique_topics, persistent_gaps, recent_abandons, topic_pivot_count}`

### File Heat Map (`file_heat_map_seq011*`)

Cross-references keystroke metrics with recently-committed pigeon files (from `pigeon_registry.json`) to build a **cognitive load map per module**.

| Constant | Value | Purpose |
|---|---|---|
| `RECENT_MSGS` | 3 | Messages after commit = "working on that file" |
| `HIGH_HES_THRESH` | 0.45 | Avg hesitation above this = "complex file" |
| `HIGH_VER_THRESH` | 5 | ≥5 versions = recurring pain point |

**Registry parsing**: Handles both raw format (`{"generated": str, "total": int, "files": [...]}`) and unpacked `{path: entry_dict}` from `load_registry()`.

**Store**: `file_heat_map.json` — flat dict, module → samples:
```json
{
  "import_rewriter": {"samples": [{"hes": 0.62, "wpm": 28.4, "state": "frustrated", "rework": "miss"}], "avg_hes": 0.55, "avg_wpm": 31.2, "miss_count": 3, "total": 8}
}
```

**Coaching feed**: `load_heat_map()` → `{modules_tracked, complex_files, high_miss_files}`

---

## DATA FLOW

### Per-message flow (VS Code extension → deep profiling)

```
User types in Pigeon Chat panel
  ↓ keydown/input events captured with delta_ms timestamps
  ↓
  ↓ on submit:
  │  extension.ts sends {events, submitted, query_text, post_response_events}
  │  ↓ spawns classify_bridge.py (subprocess, reads stdin JSON)
  │    ├─ _compute_metrics(events) → hesitation_score, wpm, del_ratio, pause_ratio
  │    ├─ OperatorStats.classify_state() → cognitive state (1 of 7)
  │    ├─ score_rework(post_response_events) → AI miss detection
  │    ├─ extract_unsaid_thoughts(events, final_text) → abandoned draft analysis
  │    ├─ record_query(query_text, submitted, unsaid) → persistent gap tracking
  │    ├─ update_heat_map(state, hesitation, rework, wpm) → module load tracking
  │    ├─ OperatorStats.ingest() → updates operator_profile.md
  │    ├─ _refresh_operator_state() → rewrites copilot-instructions.md IMMEDIATELY
  │    └─ (every 8 submitted) → _build_prompt() → DeepSeek → operator_coaching.md
  │  ↓
  │  Returns: { state, hesitation, wpm, coaching_updated, rework_verdict }
  ↓
  extension.ts reads operator-state from copilot-instructions.md
  ↓ prepended as system context to LM request
  ↓ response streamed back to chat UI
  ↓
  After response completes:
    30-second post-response capture window begins (POST_RESPONSE_WINDOW_MS)
    All keydown/input events stored as postResponseEvents[]
    Sent with NEXT submit for rework scoring
```

### Per-commit flow (git post-commit hook)

```
git commit -m "fix: timeout on buffer polling"
  ↓ git_plugin.py fires automatically (post-commit hook)
  ↓
  1.  _commit_msg() → parse intent slug
  2.  _changed_files() → list pigeon files touched
  3.  For each: docstring → desc, bump version, update date
  4.  rewrite_all_imports() ← BEFORE file renames (critical ordering)
  5.  Rename files on disk (version bump, date, desc, intent)
  6.  _inject_box() → prompt box headers in each file
  7.  Log to pigeon_sessions/{name}.jsonl
  8.  Update pigeon_registry.json (token history, version, date)
  9.  Rebuild MANIFEST.md (per-folder + MASTER)
  10. _refresh_copilot_instructions() → auto-index section (85+ modules)
  11. Load deep signals: rework_log.json + query_memory.json + file_heat_map.json
  12. _build_commit_coaching_prompt() → enhanced with deep signal sections
  13. _generate_commit_coaching() → DeepSeek → operator_coaching.md
  14. Inject operator-state into copilot-instructions.md
  15. Auto-commit [pigeon-auto]
```

### Coaching synthesis prompt structure

The DeepSeek coaching prompt (both in `classify_bridge.py` and `git_plugin.py`) includes these sections when data exists:

1. **Operator History** — last N messages with states, hesitation scores, WPM
2. **AI Response Quality** — miss rate, miss count from `rework_log.json`
3. **Persistent Gaps** — recurring unresolved questions from `query_memory.json`
4. **Abandoned/Unsaid Themes** — deleted drafts + emotional deletions
5. **File Complexity Debt** — modules causing highest cognitive load from `file_heat_map.json`
6. **High AI-Miss Files** — modules where AI answers consistently fail
7. **Registry Churn** (commit-time only) — most frequently modified files

---

## VS CODE EXTENSION

### Architecture

```
vscode-extension/
├── src/extension.ts           # PigeonChatPanel class + classify bridge
│                              #   classifySession(root, events, submitted, queryText, postResponseEvents)
│                              #   readOperatorState(root) — reads copilot-instructions.md
│                              #   ClassifyResult interface: {state, hesitation, wpm, rework_verdict?}
├── media/chat.html            # Chat UI with keystroke capture
│                              #   postResponseEvents[], capturePostResponse flag
│                              #   POST_RESPONSE_WINDOW_MS = 30000
├── classify_bridge.py         # Python orchestrator (373 lines)
│                              #   LLM_REWRITE_EVERY = 8
│                              #   Calls all deep signal modules
└── package.json               # Extension manifest
```

### Model priority

1. `vscode.lm` API — uses whatever Copilot model is active
2. DeepSeek fallback — requires `DEEPSEEK_API_KEY` in environment

### Build & Launch

```bash
cd vscode-extension && npm install && npm run compile
# F5 → Extension Development Host → Ctrl+Shift+P → "Pigeon: Open Keystroke-Aware Chat"
```

---

## DATA FORMATS

### Event types (keystroke_telemetry/v2)

| Event Type | Description | Delta source |
|---|---|---|
| `insert` | Character typed | Time since last event |
| `delete` / `backspace` | Character removed | Time since last event |
| `paste` | Clipboard paste | delta_ms = 0 |
| `cut` | Clipboard cut | Time since last event |
| `clear` | Ctrl+A+Del or similar | Time since last event |
| `undo` / `redo` | Undo/redo action | Time since last event |
| `submit` | Message submitted | Time since last event |

### Per-event JSON (`events_{session}.jsonl`)

```json
{"schema": "keystroke_telemetry/v2", "timestamp_ms": 1710561234567, "event_type": "insert", "key": "h", "cursor_pos": 5, "buffer": "hello", "message_id": "a1b2c3", "delta_ms": 154}
```

### Session summary (`summary_{session}.json`)

```json
{"message_id": "a1b2c3", "submitted": true, "deleted": false, "final_text": "hello world", "keystroke_count": 15, "delete_count": 3, "pause_count": 1, "hesitation_score": 0.289}
```

### Pigeon registry (`pigeon_registry.json`)

```json
{
  "generated": "2026-03-16T05:43:00Z",
  "total": 85,
  "files": [{
    "path": "src/rework_detector_seq009_v003_d0316__...py",
    "name": "rework_detector", "seq": 9, "ver": 3, "date": "0316",
    "desc": "measures_ai_answer_quality_from", "intent": "fix_deep_signal",
    "tokens": 1024,
    "history": [{"ver": 1, "date": "0315"}, {"ver": 2, "date": "0316"}, {"ver": 3, "date": "0316"}]
  }]
}
```

### Deep signal stores

| File | Format | Key fields |
|---|---|---|
| `rework_log.json` | Plain JSON array | `[{ts, verdict, rework_score, del_ratio, wpm, query_hint}]` |
| `query_memory.json` | JSON object | `{queries: [{ts, text, fingerprint, submitted}], abandoned_themes: [{ts, text, state}]}` |
| `file_heat_map.json` | Flat JSON dict | `{module_name: {samples, avg_hes, avg_wpm, miss_count, total}}` |
| `operator_coaching.md` | Markdown + HTML comments | `<!-- coaching:count=N -->` header + 5 coaching bullets |
| `operator_profile.md` | Markdown tables | Metric ranges, state distribution, time-of-day profile |

---

## CONSTANTS & THRESHOLDS

| Constant | Value | Module | Purpose |
|---|---|---|---|
| `SCHEMA_VERSION` | `"keystroke_telemetry/v2"` | logger | Event schema version |
| `PAUSE_THRESHOLD_MS` | 2,000 | logger | Inter-key gap → "pause" event |
| `REWORK_WINDOW_MS` | 30,000 | rework_detector | Post-response capture window |
| `HEAVY_DEL_RATIO` | 0.35 | rework_detector | Deletion rate threshold for rework |
| `RECUR_THRESH` | 3 | query_memory | Same fingerprint N times = gap |
| `MAX_ENTRIES` | 500 | query_memory | Circular buffer size |
| `RECENT_MSGS` | 3 | file_heat_map | Messages after commit = working |
| `HIGH_HES_THRESH` | 0.45 | file_heat_map | Avg hesitation → "complex file" |
| `HIGH_VER_THRESH` | 5 | file_heat_map | ≥5 versions = pain point |
| `LLM_REWRITE_EVERY` | 8 | classify_bridge | Coaching synthesis frequency |
| `PIGEON_MAX` | 200 | compiler | Hard line cap (auto-split above) |
| `PIGEON_RECOMMENDED` | 50 | compiler | Target lines per output file |
| `PIGEON_HARD_CAP_LINES` | 88 | context_budget | Scorer flags above this |
| `TOKEN_RATIO` | 4 | git_plugin | Chars per token (GPT/Claude avg) |
| `POST_RESPONSE_WINDOW_MS` | 30,000 | chat.html | Post-response event capture |

---

## TEST STATUS

### Core tests (`py test_all.py` — zero deps, stdlib only)

| Test | Description | Status |
|------|-------------|--------|
| TEST 1 | Telemetry Logger — v2 schema, 3 turns, submit + discard | PASS |
| TEST 2 | Context Budget Scorer — hard cap, budget, coupling | PASS |
| TEST 3 | Drift Watcher — baseline + versioned filename drift detection | PASS |
| TEST 4 | Resistance Bridge — telemetry → compiler signal | PASS |

### Deep profiling E2E tests (`py deep_test.py` — validates full pipeline)

| Test | Description | Status |
|------|-------------|--------|
| TEST 1 | Full pipeline — neutral state, hesitation + WPM computation | PASS |
| TEST 2 | Rework detector — heavy deletion → verdict=miss, del_ratio > 0.35 | PASS |
| TEST 3 | Query memory — 5 entries, recurring fingerprint detected (count=3) | PASS |
| TEST 4 | Query memory aggregates — total_queries, unique_topics | PASS |
| TEST 5 | File heat map — 3 modules tracked from pigeon_registry.json | PASS |
| TEST 6 | Rework persistence — rework_log.json written, verdict correct | PASS |
| TEST 7 | Coaching aggregates — persistent_gaps with recurring data | PASS |
| TEST 8 | Bridge output — all 5 fields: state, hesitation, wpm, coaching_updated, rework_verdict | PASS |

```bash
py test_all.py   # 4 core tests — zero dependencies
py deep_test.py  # 8 deep profiling tests — validates full signal pipeline
```

---

## OPERATOR KEYSTROKE TRAIL

*Last 50 keystrokes | auto-synced by manifest_builder | 2026-03-22 19:40 UTC*

> **How to read**: Each row is one keystroke event from the operator.
> Markers flag cognitive signals: ⏸ = long pause (>2s), 
> ⌫ = backspace burst (3+), ✓ = submitted, 🗑 = discarded.
> Hesitation scores come from session summaries (0.0 = confident, 1.0 = max hesitation).

| # | Key | Event | Δms | Buffer | Markers |
|---|-----|-------|----:|--------|---------|
| 1 | `What is the meaning of life?` | paste | 0 | `What is the meaning of life?` |  |
| 2 | `?` | backspace | 0 | `What is the meaning of life` | ⌫ burst |
| 3 | `e` | backspace | 47 | `What is the meaning of lif` | ⌫ burst |
| 4 | `f` | backspace | 58 | `What is the meaning of li` | ⌫ burst |
| 5 | `i` | backspace | 48 | `What is the meaning of l` | ⌫ burst |
| 6 | `l` | backspace | 45 | `What is the meaning of ` | ⌫ burst |
| 7 | `4` | insert | 49 | `What is the meaning of 4` |  |
| 8 | `2` | insert | 164 | `What is the meaning of 42` |  |
| 9 | `?` | insert | 195 | `What is the meaning of 42?` |  |
| 10 | `H` | insert | 0 | `H` |  |
| 11 | `e` | insert | 151 | `He` |  |
| 12 | `l` | insert | 150 | `Hel` |  |
| 13 | `o` | insert | 151 | `Helo` |  |
| 14 | ` ` | insert | 151 | `Helo ` |  |
| 15 | `w` | insert | 154 | `Helo w` |  |
| 16 | `r` | insert | 150 | `Helo wr` |  |
| 17 | `l` | insert | 152 | `Helo wrl` |  |
| 18 | `d` | insert | 151 | `Helo wrld` |  |
| 19 | `d` | backspace | 150 | `Helo wrl` | ⌫ burst |
| 20 | `l` | backspace | 41 | `Helo wr` | ⌫ burst |
| 21 | `r` | backspace | 41 | `Helo w` | ⌫ burst |
| 22 | `w` | backspace | 41 | `Helo ` | ⌫ burst |
| 23 | `w` | insert | 42 | `Helo w` |  |
| 24 | `o` | insert | 151 | `Helo wo` |  |
| 25 | `r` | insert | 152 | `Helo wor` |  |
| 26 | `l` | insert | 206 | `Helo worl` |  |
| 27 | `d` | insert | 213 | `Helo world` |  |
| 28 | `!` | insert | 182 | `Helo world!` |  |
| 29 | `A` | insert | 0 | `A` |  |
| 30 | `c` | insert | 151 | `Ac` |  |
| 31 | `t` | insert | 150 | `Act` |  |
| 32 | `u` | insert | 151 | `Actu` |  |
| 33 | `a` | insert | 150 | `Actua` |  |
| 34 | `l` | insert | 151 | `Actual` |  |
| 35 | `l` | insert | 160 | `Actuall` |  |
| 36 | `y` | insert | 152 | `Actually` |  |
| 37 | ` ` | insert | 150 | `Actually ` |  |
| 38 | `n` | insert | 152 | `Actually n` |  |
| 39 | `v` | insert | 166 | `Actually nv` |  |
| 40 | `m` | insert | 155 | `Actually nvm` |  |
| 41 | `Ctrl+A+Del` | clear | 2260 | `` | ⏸ 2.3s |
| 42 | `What is the meaning of life?` | paste | 0 | `What is the meaning of life?` |  |
| 43 | `?` | backspace | 1 | `What is the meaning of life` | ⌫ burst |
| 44 | `e` | backspace | 44 | `What is the meaning of lif` | ⌫ burst |
| 45 | `f` | backspace | 41 | `What is the meaning of li` | ⌫ burst |
| 46 | `i` | backspace | 41 | `What is the meaning of l` | ⌫ burst |
| 47 | `l` | backspace | 41 | `What is the meaning of ` | ⌫ burst |
| 48 | `4` | insert | 43 | `What is the meaning of 4` |  |
| 49 | `2` | insert | 151 | `What is the meaning of 42` |  |
| 50 | `?` | insert | 151 | `What is the meaning of 42?` |  |

### Recent message hesitation scores

| Message | Submitted | Keys | Dels | Hesitation | State |
|---------|-----------|-----:|-----:|-----------:|-------|
| `d44d96861d` | ✓ | 19 | 4 | 0.211 | restructuring |
| `a2039d8672` | 🗑 | 13 | 0 | 0.572 | abandoned |
| `be288e9992` | ✓ | 9 | 5 | 0.556 | hesitant |
| `9236ebb5c5` | ✓ | 19 | 4 | 0.211 | restructuring |
| `40a3de951a` | 🗑 | 13 | 0 | 0.508 | abandoned |
| `9ea58fac99` | ✓ | 9 | 5 | 0.556 | hesitant |
| `e8d185c540` | ✓ | 19 | 4 | 0.211 | restructuring |
| `32ea34023c` | 🗑 | 13 | 0 | 0.528 | abandoned |
| `31fa8ab859` | ✓ | 9 | 5 | 0.556 | hesitant |
| `2ceda7e4aa` | ✓ | 19 | 4 | 0.211 | restructuring |
| `4bc3a986e8` | 🗑 | 13 | 0 | 0.572 | abandoned |
| `16f9f30911` | ✓ | 9 | 5 | 0.556 | hesitant |


## CHANGELOG

### v2.0.0 (2026-03-16)
- **Added**: Rework detector — AI answer quality scoring from post-response keystrokes (`rework_detector_seq009*`)
- **Added**: Query memory — recurring gap fingerprinting + unsaid theme persistence (`query_memory_seq010*`)
- **Added**: File heat map — cognitive load per pigeon module cross-referenced with registry (`file_heat_map_seq011*`)
- **Added**: Post-response capture window (30s) in chat.html for rework scoring
- **Added**: Deep signal sections in coaching prompt: rework stats, persistent gaps, heat map, high-miss files
- **Added**: `classify_bridge.py` full pipeline — rework + unsaid + query_memory + heat_map per message
- **Added**: `extension.ts` forwards `query_text` + `post_response_events` to classify bridge
- **Added**: `deep_test.py` — 8 E2E tests for full deep profiling pipeline
- **Fixed**: `score_rework` del_ratio — pause events no longer dilute deletion signal (keystrokes only)
- **Fixed**: `_get_recent_files` — handles both raw registry format and unpacked dict
- **Fixed**: `git_plugin` — rework_log parsed as list (not dict), heat_map parsed as flat dict
- **Fixed**: `git_plugin` — removed duplicate function definitions from prior session
- **Enhanced**: `git_plugin._build_commit_coaching_prompt` — 3 new optional deep signal sections
- **Enhanced**: `operator_coaching.md` — now includes AI Response Quality, Persistent Gaps, File Complexity Debt
- **Upgraded**: MASTER_MANIFEST.md — prompt box, deep profiling docs, data flow, constants table

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
