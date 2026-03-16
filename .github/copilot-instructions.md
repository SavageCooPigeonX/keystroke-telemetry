# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

## What this repo is

Two tools packaged together:
1. **Keystroke Telemetry** — captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls — pure signal processing.
2. **Pigeon Code Compiler** — autonomous code decomposition engine. Enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target). Filenames carry living metadata — they mutate on every commit.

**Stack**: Python 3.13 Windows (`py` launcher, never `python`). Always set `$env:PYTHONIOENCODING = "utf-8"` before running Python in terminal. DeepSeek API key in `$env:DEEPSEEK_API_KEY`.

---

## CRITICAL: Pigeon Filenames Mutate

**Every file in this repo has a versioned name that changes on commit.** Never hardcode a full filename — always use `file_search` or `glob` patterns.

### Naming convention
```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```
- `name` — module identity, never changes (e.g. `resistance_bridge`)
- `seq{NNN}` — sequence number within folder, never changes
- `v{NNN}` — version, bumps every commit the file is touched
- `d{MMDD}` — UTC date of last mutation
- `description` — what the file DOES (from docstring, auto-extracted)
- `_lc_` — separator (lifecycle marker)
- `intent` — last commit message slug (3 words max)

**To find a file**: search by `{name}_seq{NNN}*` e.g. `resistance_bridge_seq006*`

### Prompt box (auto-injected after docstring on every commit)
```python
# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 119 lines | ~1,195 tokens
# DESC:   bridge_between_keystroke_telemetry_and
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
```

### Size limits
- `PIGEON_MAX = 200` lines — hard cap, compiler will split anything over this
- `PIGEON_RECOMMENDED = 50` lines — target per file
- `PIGEON_HARD_CAP_LINES = 88` in `context_budget` scorer

### Post-commit hook
`.git/hooks/post-commit` runs `py -m pigeon_compiler.git_plugin` after every commit.
Pipeline: parse commit intent → build import_map → **rewrite imports FIRST** → rename files → inject prompt boxes → update registry → rebuild MANIFESTs → auto-commit `[pigeon-auto]`.
**Import rewrite happens BEFORE file rename** — this was a fixed bug (commit 6705b11).

---

## Data Flow: Keystroke → Cognitive State → LLM

```
Browser (client/keystroke-telemetry.js)
  ↓ HTTP POST  (schema: keystroke_telemetry/v2)
src/logger_seq003           → TelemetryLogger
  ↓ per-keystroke events     → events_{session}.jsonl
  ↓ on submit/discard        → summary_{session}.json
src/models_seq002            → KeyEvent, MessageDraft
  ↓ hesitation_score computed on _finalize_draft()
src/operator_stats_seq008    → OperatorStats  (persistent: operator_profile.md)
src/resistance_bridge_seq006 → HesitationAnalyzer.resistance_signal()
  ↓ {adjustment, reason, profile}
src/cognitive/adapter_seq001 → get_cognitive_modifier(state)
  ↓ {prompt_injection, temperature_modifier, strategy}
  ↓ ← INJECT INTO SYSTEM PROMPT + ADJUST TEMPERATURE ← (not yet wired to LLM call site)
src/drift_watcher_seq005     → DriftWatcher  (file-size drift → split signals)
src/context_budget_seq004    → score_context_budget()  (token cost scoring)
```

**Known gap**: `MessageDraft` has `hesitation_score: float` but no `state: str` field. Cognitive state is not stored back on draft. The adapter exists but isn't wired to any LLM call site yet.

---

## Seven Cognitive States

Detected by keystroke classifier. Each maps to a system prompt injection + temperature modifier.

| State | Signal | Prompt strategy | Temp Δ |
|---|---|---|---|
| `frustrated` | heavy deletions + long pauses + high hesitation | concise, 2-3 options, bullets | -0.1 |
| `hesitant` | long pauses, low wpm | warm, anticipate intent, follow-up question | +0.05 |
| `flow` | fast typing, minimal edits | match energy, technical depth, no hand-holding | +0.1 |
| `focused` | steady typing, engaged | thorough, well-structured | 0 |
| `restructuring` | heavy rewrites before submit | precise, headers/numbered, match effort | -0.05 |
| `abandoned` | deleted message, re-approached | welcoming, direct | 0 |
| `neutral` | no strong signal | standard | 0 |

`get_cognitive_modifier(state)` in `src/cognitive/adapter_seq001*` returns `{prompt_injection, temperature_modifier, strategy}`.

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
