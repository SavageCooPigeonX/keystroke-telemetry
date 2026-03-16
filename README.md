# Keystroke Telemetry + Pigeon Code Engine

Two tools, one goal: **make codebases self-documenting and LLM-readable by default.**

```
# ── pigeon ────────────────────────────────────
# PROJECT: keystroke-telemetry
# MODULES: 85+ tracked | 19 compiled packages
# STACK:   Python 3.13 (Windows) + TypeScript
# SCHEMA:  keystroke_telemetry/v2
# LINES:   ~12,000 across all modules
# STATUS:  All systems live — deep profiling active
# REPO:    github.com/SavageCooPigeonX/keystroke-telemetry
# ──────────────────────────────────────────────
```

1. **Pigeon Code Engine** — drop it into any repo. From that point on, every commit autonomously refactors files to stay under 200 lines, renames them with living metadata, rewrites all imports, writes manifests, and injects prompt boxes. The human manages intent (via commit messages). The files track everything else.

2. **Keystroke Telemetry** — captures typing patterns in LLM chat UIs, classifies operator cognitive state in real time (7 states), reconstructs unsaid thoughts, detects cross-session drift, scores AI answer quality from post-response behavior, tracks recurring question gaps, and maps cognitive load per module. Zero LLM calls for classification — pure signal processing. Files that cause the most human friction get split more aggressively.

> **Not a keylogger.** Telemetry captures events **within your own app's text field** and runs locally. No data leaves the machine.

---

## Table of Contents

- [The Vision](#the-vision-full-plug-and-play)
- [Pigeon Code Engine](#pigeon-code-how-it-works)
  - [Filename Convention](#filenames-are-the-changelog)
  - [Commit Pipeline](#what-happens-on-every-commit-automated-pipeline)
  - [Prompt Box Format](#prompt-box-auto-injected-after-every-commit)
  - [Compiler Phases](#the-compiler-oversized-files-get-split-automatically)
  - [CLI Commands](#cli)
  - [Token Savings](#token-savings)
- [Keystroke Telemetry](#keystroke-telemetry)
  - [Pipeline Overview](#capture--classify--inject--learn)
  - [Seven Cognitive States](#seven-cognitive-states)
  - [Browser Capture](#browser-capture)
  - [Deep Profiling System](#deep-profiling-system-v2)
    - [Rework Detector](#rework-detector)
    - [Query Memory](#query-memory--persistent-gap-tracker)
    - [File Heat Map](#file-heat-map--cognitive-load-per-module)
    - [Unsaid Thoughts](#unsaid-thoughts-reconstruction)
    - [Cross-Session Drift](#cross-session-drift-detection)
  - [Operator Profile](#self-growing-operator-profile)
  - [Resistance Bridge](#resistance-bridge-telemetry-feeds-the-compiler)
  - [Coaching Synthesis](#coaching-synthesis-llm-powered)
- [VS Code Extension](#vs-code-extension-pigeon-chat)
  - [Architecture](#extension-architecture)
  - [Message Flow](#what-runs-on-every-message)
  - [Post-Response Capture](#post-response-capture-window)
  - [Build & Launch](#build--launch)
- [Data Formats](#data-formats)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Current Status](#current-status)
- [Quick Start](#quick-start)

---

## The Vision: Full Plug-and-Play

The end state is a single `pigeon init` that makes any git repo self-maintaining:

```
git commit -m "fix: timeout on retries"
           ↓
  Pigeon reads your commit message
           ↓
  Renames touched files with new version + intent slug
  Rewrites every import across the codebase
  Injects prompt box headers (token count, desc, intent, last commit)
  Updates pigeon_registry.json
  Rebuilds every MANIFEST.md
  Refreshes .github/copilot-instructions.md with live module index
  Refreshes .github/copilot-instructions.md with operator cognitive state
  Generates DeepSeek-powered behavioral coaching from deep signals
  Auto-commits [pigeon-auto]
```

**What you provide**: intent (the commit message).  
**What the files provide**: description (from docstring), version history, token cost, mutation log.  
**What the compiler provides**: size enforcement, import consistency, LLM-readable output.  
**What the telemetry provides**: cognitive state, rework rate, recurring gaps, module anxiety map.

The human is never a bottleneck. The codebase documents itself.

---

## Pigeon Code: How It Works

### Filenames are the changelog

```
noise_filter_seq007_v004_d0316__filter_live_noise_lc_fixed_timeout.py
├─ noise_filter      = module identity (never changes)
├─ seq007            = sequence in folder (never changes)
├─ v004              = 4th time this file was touched
├─ d0316             = last mutated March 16
├─ filter_live_noise = what this file DOES (from docstring, auto-extracted)
└─ fixed_timeout     = what was LAST DONE (from commit message, 3 words max)
```

An LLM agent `ls`-ing this folder knows the entire version history, purpose, and last change of every file — without opening a single one.

### What happens on every commit (automated pipeline)

```
git commit -m "fix: timeout on buffer polling"
     ↓
 git_plugin.py fires (post-commit hook)
     ↓
 1.  Parse commit message → intent slug ("timeout_buffer_polling")
 2.  For each changed pigeon .py file:
     · Read docstring → desc slug
     · Bump version, update date
     · Build import_map {old_module → new_module}
 3.  Rewrite all imports across codebase  ← BEFORE renaming
 4.  Rename files on disk
 5.  Inject/update prompt boxes (SEQ, VER, lines, tokens, DESC, INTENT, LAST, SESSIONS)
 6.  Log to logs/pigeon_sessions/{name}.jsonl
 7.  Update pigeon_registry.json (token history, version, date, desc, intent)
 8.  Rebuild all MANIFEST.md files (per-folder + MASTER)
 9.  Refresh .github/copilot-instructions.md auto-index (85+ modules searchable)
10.  Load deep signals: rework_log.json + query_memory.json + file_heat_map.json
11.  Generate DeepSeek coaching prompt with deep signal sections
12.  Write operator_coaching.md + refresh copilot-instructions.md operator state
13.  Auto-commit [pigeon-auto]
```

The import rewrite always happens *before* file rename — the codebase is never left in a broken import state. This was a fixed bug (commit `6705b11`).

### Prompt box (auto-injected after every commit)

```python
# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v004 | 85 lines | ~2,100 tokens
# DESC:   filter_live_noise
# INTENT: fixed_timeout
# LAST:   2026-03-16 @ a3f2b1c
# SESSIONS: 4
# ──────────────────────────────────────────────
```

Every file announces itself: seq, version, line count, token cost, what it does, what changed last, and how many times it's been touched across its lifetime.

### Naming convention

```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```

| Part | Meaning | Source | Mutates? |
|---|---|---|---|
| `name` | Module identity | Developer-defined | Never |
| `seq{NNN}` | Sequence within folder | Auto-assigned | Never |
| `v{NNN}` | Version | Auto-incremented on every touch | Every commit |
| `d{MMDD}` | Date of last mutation | UTC today | Every commit |
| `description` | What the file DOES | Extracted from docstring | On docstring change |
| `_lc_` | Lifecycle separator | Fixed | Never |
| `intent` | What was LAST DONE | Commit message, 3 words max | Every commit |

**Critical**: never hardcode full pigeon filenames — they change on every commit. Search by `{name}_seq{NNN}*` glob pattern.

### Size limits

| Constant | Value | Meaning |
|---|---|---|
| `PIGEON_MAX` | 200 lines | Hard cap — compiler auto-splits anything over |
| `PIGEON_RECOMMENDED` | 50 lines | Target per output file after compilation |
| `PIGEON_HARD_CAP_LINES` | 88 lines | `context_budget` scorer flags above this |

### The compiler: oversized files get split automatically

When a file exceeds 200 lines, the compiler runs:

```
Oversized file (e.g. 394 lines)
   ↓
Phase 1  — AST decompose oversized functions (free, no LLM)
           Extracts top-level functions by AST node boundaries.
Phase 1b — Class decomposition via DeepSeek (~$0.001)
           Extracts methods as standalone functions, keeps class thin.
Phase 2  — DeepSeek generates a cut plan with exact line assignments
           Returns JSON: file boundaries, function groupings, shared state.
Phase 3  — Deterministic bin-packing → N files × ≤50 lines
           Writes __init__.py (re-exports), MANIFEST.md, pigeon-named files.
```

The compiler compiles itself — every module in `pigeon_compiler/` was split by running the compiler on its own source.

```bash
# Compile one file:
py -m pigeon_compiler.runners.run_clean_split_seq010* path/to/big_file.py

# Compile entire codebase:
py -m pigeon_compiler.runners.run_batch_compile_seq015* --dry-run
py -m pigeon_compiler.runners.run_batch_compile_seq015*

# Self-heal pipeline (fix broken imports, re-inject prompt boxes):
py -m pigeon_compiler.runners.run_heap_seq010*

# Full pigeon loop (refactor until compliant):
py -m pigeon_compiler.runners.run_pigeon_loop_seq009*
```

### CLI

| Command | What it does |
|---|---|
| `pigeon init` | Install git hooks, create registry + session dir |
| `pigeon status` | Files, tokens, stale count, hook status, session count |
| `pigeon heal` | Bulk inject prompt boxes + rebuild manifests |
| `pigeon sessions` | Show mutation audit trail across all files |
| `pigeon uninstall` | Remove hooks (preserves registry + logs) |

### Token savings

An LLM agent reads only `@pigeon` preambles and `MANIFEST.md` files to build a project map — without opening source files.

On a 400-file codebase: **10K–35K tokens saved per session**, ~200K–700K/day, **$15–$150/month** depending on model.

---

## Keystroke Telemetry

### Capture → Classify → Inject → Learn

The full pipeline from keystroke to AI behavioral adaptation:

```
Browser keystrokes (keydown/input events with timestamps)
      ↓
  TelemetryLogger (schema: keystroke_telemetry/v2)
      ↓  per-keystroke → events_{session}.jsonl
      ↓  on finalize  → summary_{session}.json
      ↓
  classify_bridge.py (_compute_metrics)
      ↓  wpm, del_ratio, pause_ratio → hesitation_score
      ↓
  OperatorStats.classify_state()
      ↓  → one of 7 cognitive states
      ↓
  ┌─────────────────────────────────────────────────────────┐
  │  DEEP PROFILING (runs on every message)                 │
  │                                                         │
  │  score_rework(post_response_events)                     │
  │    → rework_log.json (AI miss rate attribution)         │
  │                                                         │
  │  record_query(query_text, submitted, unsaid_analysis)   │
  │    → query_memory.json (recurring gap fingerprints)     │
  │                                                         │
  │  update_heat_map(state, hesitation, rework, wpm)        │
  │    → file_heat_map.json (cognitive load per module)     │
  └─────────────────────────────────────────────────────────┘
      ↓
  get_cognitive_modifier(state)
      ↓  → { prompt_injection, temperature_modifier, strategy }
      ↓
  Inject into LLM system prompt + adjust temperature
      ↓
  (every 8 submitted messages)
  _build_prompt(history, rework_stats, query_mem, heat_map)
      ↓  → DeepSeek synthesizes behavioral coaching
      ↓  → operator_coaching.md
      ↓  → injected into .github/copilot-instructions.md
```

### Seven cognitive states

Classified from typing patterns alone — zero LLM calls:

| State | Detection Signal | Prompt Adaptation | Temp Δ |
|---|---|---|---|
| `frustrated` | Heavy deletions + long pauses + high hesitation | Concise, 2-3 options, bullets | −0.1 |
| `hesitant` | Long inter-key pauses, low WPM | Warm, anticipate intent, follow-up question | +0.05 |
| `flow` | Fast typing, minimal edits | Match energy, full technical depth, no hand-holding | +0.1 |
| `focused` | Steady, deliberate, engaged | Thorough, well-structured | 0 |
| `restructuring` | Heavy rewrite before submit | Precise, headers/numbered, match effort | −0.05 |
| `abandoned` | Deleted entire message, re-approached | Welcoming, direct | 0 |
| `neutral` | No strong signal | Standard | 0 |

State classification is handled by `OperatorStats.classify_state()` using these thresholds:
- **Hesitation score** = `pause_ratio × 0.4 + deletion_ratio × 0.35 + (1 - submit_rate) × 0.25`
- **Pause detection** = inter-key gap > 2,000ms (`PAUSE_THRESHOLD_MS`)
- **Deletion burst** = 3+ consecutive backspace/delete events

### Browser capture

```javascript
KeystrokeTelemetry.attach('chat-input', {
    agentType: 'assistant',
    flushEndpoint: '/api/telemetry/keystrokes'
});

const result = await KeystrokeTelemetry.onSubmit('chat-input', finalText);
// → { cognitive_state: 'frustrated', hesitation_score: 0.62 }
```

Schema: `keystroke_telemetry/v2`. Auto-flushes at 200 events. Abandon detection at 30s blur timeout. Paste tracking. Cognitive pause detection (>2s gaps).

**Event types captured**: `insert`, `delete`, `backspace`, `paste`, `cut`, `clear`, `undo`, `redo`, `submit`

**Per-event data**: `timestamp_ms`, `event_type`, `key`, `cursor_pos`, `buffer_snapshot`, `message_id`, `delta_ms`

---

### Deep Profiling System (v2)

Three modules that run on every message, building persistent stores that feed into coaching synthesis:

#### Rework Detector

**Module**: `rework_detector_seq009*` (~106 lines)

Scores AI answer quality by watching what the operator does in the 30 seconds **after** receiving a response. If the operator immediately starts deleting heavily and retyping, the AI's answer was a "miss."

```python
from src.rework_detector import score_rework, record_rework, load_rework_stats

# Score post-response events (captured in 30s window after AI responds)
score = score_rework(post_response_events)
# → {
#     'rework_score': 0.573,
#     'del_ratio': 0.818,      # 81.8% of keystrokes were deletes
#     'wpm': 42.3,
#     'verdict': 'miss'        # AI answer was bad
# }

# Persist to rework_log.json
record_rework(root, score, query_text="how do I verify deepseek integration")

# Load aggregate stats for coaching prompt
stats = load_rework_stats(root)
# → {
#     'miss_rate': 0.33,        # 33% of responses were misses
#     'miss_count': 4,
#     'total_responses': 12,
#     'worst_queries': ['how do I verify deepseek...']
# }
```

**Thresholds**:
| Constant | Value | Meaning |
|---|---|---|
| `REWORK_WINDOW_MS` | 30,000 | 30s post-response capture window |
| `HEAVY_DEL_RATIO` | 0.35 | Deletion rate above this = rework signal |
| Miss trigger | `rework_score > 0.55 OR del_ratio > 0.35` | Classifies as "miss" |

**Verdict logic**:
- `miss` — heavy rework, AI answer wasn't useful
- `partial` — moderate rework, answer was partially helpful
- `ok` — minimal rework, answer was good

**Storage format** (`rework_log.json`): Plain JSON array, not wrapped in an object:
```json
[
  {"ts": 1710561234, "verdict": "miss", "rework_score": 0.573, "del_ratio": 0.818, "wpm": 42.3, "query_hint": "how do I verify deepseek"},
  {"ts": 1710561456, "verdict": "ok", "rework_score": 0.12, "del_ratio": 0.05, "wpm": 38.1, "query_hint": "list all modules"}
]
```

**Key design decision**: `del_ratio = len(deletes) / max(len(inserts) + len(deletes), 1)` — only counts actual keystrokes, not pause events. This prevents "thinking pauses" from diluting the deletion signal.

---

#### Query Memory & Persistent Gap Tracker

**Module**: `query_memory_seq010*` (~118 lines)

Fingerprints every query the operator sends. If the same semantic question appears 3+ times (detected by order-invariant word fingerprinting), it's flagged as a "persistent gap" — a topic the AI consistently fails to resolve. Also captures abandoned draft themes from the unsaid module.

```python
from src.query_memory import record_query, load_query_memory

# Record a submitted query with unsaid analysis
record_query(root, "how do I verify deepseek integration", submitted=True, unsaid=unsaid_analysis)

# Load aggregate for coaching
mem = load_query_memory(root)
# → {
#     'total_queries': 47,
#     'unique_topics': 23,
#     'persistent_gaps': [
#         {'query': 'how do I verify deepseek integration', 'count': 5}
#     ],
#     'recent_abandons': ['I already tried that but...'],
#     'topic_pivot_count': 3
# }
```

**Fingerprinting algorithm** (`_fingerprint(text)`):
1. Lowercase, strip punctuation
2. Remove filler words (`the`, `a`, `is`, `how`, `do`, `I`, etc.)
3. Take first 8 remaining words
4. Sort alphabetically → creates order-invariant hash

This means "how do I verify deepseek integration" and "verify deepseek integration how" produce the **same** fingerprint.

**Thresholds**:
| Constant | Value | Meaning |
|---|---|---|
| `RECUR_THRESH` | 3 | Same fingerprint N times = persistent gap |
| `MAX_ENTRIES` | 500 | Circular buffer, oldest evicted |

**Storage format** (`query_memory.json`):
```json
{
  "queries": [
    {"ts": 1710561234, "text": "how do I verify deepseek", "fingerprint": "deepseek integration verify", "submitted": true}
  ],
  "abandoned_themes": [
    {"ts": 1710561100, "text": "I already tried that", "state": "frustrated"}
  ]
}
```

---

#### File Heat Map — Cognitive Load Per Module

**Module**: `file_heat_map_seq011*` (~139 lines)

Cross-references keystroke metrics with recently-committed pigeon files (via `pigeon_registry.json`) to build a **cognitive load map**. Identifies which modules spike hesitation, slow typing, or consistently trigger AI misses.

```python
from src.file_heat_map import update_heat_map, load_heat_map

# Called after every message — associates metrics with recent files
update_heat_map(root, state="frustrated", hesitation=0.62, rework_verdict="miss", wpm=28.4)

# Load aggregate for coaching
hm = load_heat_map(root)
# → {
#     'modules_tracked': 12,
#     'complex_files': ['import_rewriter', 'plan_validator'],   # avg_hes > 0.45
#     'high_miss_files': ['context_budget']                     # miss_count / total > 0.3
# }
```

**How it determines "which files you're working on"**:
1. Reads `pigeon_registry.json`
2. Handles both raw format (`{"generated": str, "total": int, "files": [...]}`) and unpacked `{path: entry_dict}` format
3. Sorts by version number descending
4. Takes top N most-recently-versioned files (`RECENT_MSGS = 3`)
5. Associates current message metrics with those files

**Thresholds**:
| Constant | Value | Meaning |
|---|---|---|
| `RECENT_MSGS` | 3 | Messages after commit = "working on that file" |
| `HIGH_HES_THRESH` | 0.45 | Average hesitation above this = "complex file" |
| `HIGH_VER_THRESH` | 5 | ≥5 versions = recurring pain point |

**Storage format** (`file_heat_map.json`): flat dict, module name → sample data:
```json
{
  "import_rewriter": {
    "samples": [{"hes": 0.62, "wpm": 28.4, "state": "frustrated", "rework": "miss"}],
    "avg_hes": 0.55,
    "avg_wpm": 31.2,
    "miss_count": 3,
    "total": 8
  }
}
```

---

#### Unsaid thoughts reconstruction

**Module**: `unsaid_seq002*` → compiled package `src/cognitive/unsaid/` (9 files)

Recovers what the operator typed but deleted — the messages they almost sent:

```python
from src.cognitive.unsaid import extract_unsaid_thoughts

unsaid = extract_unsaid_thoughts(keystroke_events, final_text)
# → {
#     'abandoned_drafts': ['I already tried that...'],
#     'emotional_deletions': [{'text': 'this is ridiculous', 'emotion': 'frustration'}],
#     'topic_pivots': 2,
#     'confidence': 0.74
# }
```

Abandoned drafts and emotional deletions are fed into `record_query()` and stored as `abandoned_themes` in `query_memory.json`.

---

#### Cross-session drift detection

**Module**: `drift_seq003*` → compiled package `src/cognitive/drift/` (7 files)

Detects frustration escalation, flow streaks, and engagement decline by comparing current session against the operator's personal baseline:

```python
from src.cognitive.drift import detect_session_drift, build_cognitive_context

drift = detect_session_drift(session_summaries, baseline)
# → { frustration_escalating: True, engagement_trend: 'declining' }

context = build_cognitive_context(session_summaries, baseline)
# → Full narrative for LLM system prompt
```

---

### Self-growing operator profile

**Module**: `operator_stats_seq008*` (~394 lines) → compiled package `src/operator_stats/` (14 files)

Written to `operator_profile.md` on every message and **auto-injected into `.github/copilot-instructions.md`** on every pigeon commit:

```markdown
**Dominant: `abandoned`** | Submit: 0% | WPM: 25.3 | Del: 26.5% | Hes: 0.309

This operator just built a fix for deep signal tracking, but their abandoned
typing with high deletion and hesitation reveals late-night frustration.
- **Anticipate deep signal debugging**: proactively surface related imports
- **Counter high rework rate**: validate flow against fixed versions first
- **Reduce hesitation on heavy edits**: scaffold a stepwise debug plan
```

The profile includes:
- **Metric ranges**: min/max/avg for WPM, deletion %, hesitation, pause duration
- **State distribution**: count and percentage of each cognitive state
- **Time-of-day profile**: morning/afternoon/evening behavioral patterns
- **Dominant state + submit rate**: overall behavioral summary

Copilot reads this at the start of every session — no manual context-setting required.

### Resistance bridge: telemetry feeds the compiler

**Module**: `resistance_bridge_seq006*` (~119 lines)

Files that cause the most human hesitation get a resistance score bump — the compiler splits them more aggressively:

```python
from src.resistance_bridge import HesitationAnalyzer

signal = HesitationAnalyzer("logs").resistance_signal()
# → {"adjustment": 0.195, "reason": "high hesitation (0.428); high discard (0.333)"}
```

The adjustment is added to the file's resistance score in the compiler's `state_extractor`. Higher resistance = more likely to be split.

### Coaching synthesis (LLM-powered)

Every 8 submitted messages, `classify_bridge.py` calls DeepSeek to synthesize all deep signals into behavioral coaching:

**Prompt includes**:
1. **Operator history** — last N messages with states, scores, WPM
2. **AI Response Quality** — miss rate, miss count, worst queries (from `rework_log.json`)
3. **Persistent Gaps** — recurring questions never resolved (from `query_memory.json`)
4. **Abandoned/Unsaid Themes** — what the operator deletes before sending
5. **File Complexity Debt** — modules causing highest cognitive load (from `file_heat_map.json`)
6. **High AI-Miss Files** — modules where AI answers consistently fail

**Output**: 5 bullet-point behavioral coaching instructions written to `operator_coaching.md` and injected into `copilot-instructions.md`.

**At commit time**, `git_plugin.py` runs a **second coaching synthesis** that also includes registry churn data (which files are being modified most frequently) and commit context.

---

## VS Code Extension: Pigeon Chat

A custom chat panel with full keystroke telemetry embedded. **Closes the loop** — every message you type is classified and injected into the model's system context *before* it responds.

### Extension architecture

```
vscode-extension/
├── src/extension.ts       # PigeonChatPanel + LM bridge (Copilot → DeepSeek fallback)
├── media/chat.html        # Chat UI with inline keystroke capture + post-response tracking
├── classify_bridge.py     # Python orchestrator → all deep signal modules → coaching
├── package.json           # Extension manifest
└── tsconfig.json          # TypeScript config
```

### What runs on every message

```
User types in Pigeon Chat panel
  ↓ keydown/input events captured with delta_ms timestamps
  ↓
  ↓ on submit:
  │  extension.ts sends {events, submitted, query_text, post_response_events} to classify_bridge.py
  │  ↓
  │  classify_bridge.py (spawned as subprocess, reads stdin JSON)
  │    ├─ _compute_metrics(events) → hesitation_score, wpm, del_ratio, pause_ratio
  │    ├─ OperatorStats.classify_state() → cognitive state
  │    ├─ score_rework(post_response_events) → AI miss detection
  │    ├─ extract_unsaid_thoughts() → abandoned draft analysis
  │    ├─ record_query(query_text, submitted, unsaid) → persistent gap tracking
  │    ├─ update_heat_map(state, hesitation, rework, wpm) → module load tracking
  │    ├─ OperatorStats.ingest() → updates operator_profile.md
  │    ├─ _refresh_operator_state() → rewrites copilot-instructions.md IMMEDIATELY
  │    └─ (every 8 submitted) → DeepSeek synthesis → operator_coaching.md
  │  ↓
  │  Returns JSON: { state, hesitation, wpm, coaching_updated, rework_verdict }
  ↓
  extension.ts reads operator-state from copilot-instructions.md
  ↓ prepended as system context to LM request
  ↓ response streamed back to chat panel
  ↓
  After response completes:
    30-second post-response capture window begins
    All keydown/input events stored as postResponseEvents[]
    Sent with NEXT submit for rework scoring
```

No git commit needed for the context update — writes direct to disk on every message.

### Post-response capture window

After the AI sends a response, `chat.html` opens a **30-second capture window** (`POST_RESPONSE_WINDOW_MS = 30000`). Every keystroke/input event during this window is captured into `postResponseEvents[]`. On the next submit, these events are sent alongside the new message's events.

This is how the rework detector knows what happened *after* the AI responded — it scores the post-response typing behavior.

### Build & Launch

```bash
cd vscode-extension
npm install
npm run compile
# Then press F5 in VS Code → Extension Development Host opens
# Ctrl+Shift+P → "Pigeon: Open Keystroke-Aware Chat"
```

**Model priority**:
1. `vscode.lm` API — uses whatever Copilot model is active
2. DeepSeek fallback — set `DEEPSEEK_API_KEY` in environment

**TypeScript interfaces**:
```typescript
interface ClassifyResult {
    state: string;        // one of 7 cognitive states
    hesitation: number;   // 0.0 (confident) → 1.0 (max hesitation)
    wpm: number;          // words per minute
    rework_verdict?: string;  // 'miss' | 'partial' | 'ok'
}
```

---

## Data Formats

### Event log (`events_{session}.jsonl`)

One JSON object per line, per keystroke:
```json
{"schema": "keystroke_telemetry/v2", "timestamp_ms": 1710561234567, "event_type": "insert", "key": "h", "cursor_pos": 5, "buffer": "hello", "message_id": "a1b2c3", "delta_ms": 154}
```

### Session summary (`summary_{session}.json`)

One JSON object per message:
```json
{"message_id": "a1b2c3", "submitted": true, "deleted": false, "final_text": "hello world", "keystroke_count": 15, "delete_count": 3, "pause_count": 1, "hesitation_score": 0.289}
```

### Pigeon registry (`pigeon_registry.json`)

```json
{
  "generated": "2026-03-16T05:43:00Z",
  "total": 85,
  "files": [
    {
      "path": "src/rework_detector_seq009_v003_d0316__measures_ai_answer_quality_from_lc_fix_deep_signal.py",
      "name": "rework_detector",
      "seq": 9,
      "ver": 3,
      "date": "0316",
      "desc": "measures_ai_answer_quality_from",
      "intent": "fix_deep_signal",
      "tokens": 1024,
      "history": [{"ver": 1, "date": "0315"}, {"ver": 2, "date": "0316"}, {"ver": 3, "date": "0316"}]
    }
  ]
}
```

### Deep signal stores

| File | Format | Schema |
|---|---|---|
| `rework_log.json` | Plain JSON array | `[{ts, verdict, rework_score, del_ratio, wpm, query_hint}]` |
| `query_memory.json` | JSON object | `{queries: [{ts, text, fingerprint, submitted}], abandoned_themes: [{ts, text, state}]}` |
| `file_heat_map.json` | Flat JSON dict | `{module_name: {samples: [...], avg_hes, avg_wpm, miss_count, total}}` |

---

## Testing

### Core tests (zero deps, stdlib only)

```bash
py test_all.py   # 4 tests, all must pass
```

| Test | Covers | What it validates |
|---|---|---|
| TEST 1 | TelemetryLogger | v2 schema, 3 turns (submit + discard + submit), event/summary file output |
| TEST 2 | Context Budget Scorer | Hard cap detection, budget scoring, coupling analysis |
| TEST 3 | DriftWatcher | Baseline comparison + versioned filename drift detection |
| TEST 4 | Resistance Bridge | Telemetry → compiler resistance signal computation |

### Deep profiling E2E tests

```bash
py deep_test.py   # 8 tests, validates full deep signal pipeline
```

| Test | Covers | What it validates |
|---|---|---|
| TEST 1 | Full pipeline | Neutral state classification, hesitation + WPM computation |
| TEST 2 | Rework detector | Heavy deletion → `verdict=miss`, del_ratio > 0.35 |
| TEST 3 | Query memory | 5 entries stored, recurring fingerprint detected (count=3) |
| TEST 4 | Query memory aggregates | total_queries, unique_topics, abandoned_themes counts |
| TEST 5 | File heat map | 3 modules tracked from pigeon_registry.json |
| TEST 6 | Rework persistence | rework_log.json written, verdict and del_ratio correct |
| TEST 7 | Coaching aggregates | persistent_gaps populated with recurring query data |
| TEST 8 | Bridge output fields | All 5 fields present: state, hesitation, wpm, coaching_updated, rework_verdict |

---

## Project Structure

```
keystroke-telemetry/
├── .github/
│   └── copilot-instructions.md      # Auto-mutating LLM context (2 auto-sections):
│                                     #   <!-- pigeon:auto-index --> — 85+ module search table
│                                     #   <!-- pigeon:operator-state --> — live cognitive profile
│
├── client/
│   └── keystroke-telemetry.js        # Browser IIFE: attach/onSubmit/getLastState (~210 lines)
│
├── src/                              # Core telemetry + cognitive layer
│   ├── timestamp_utils_seq001*       # _now_ms — millisecond epoch utility (8 lines)
│   ├── models_seq002*                # KeyEvent, MessageDraft dataclasses (39 lines)
│   ├── logger_seq003*                # TelemetryLogger, SCHEMA_VERSION (158 lines)
│   ├── context_budget_seq004*        # score_context_budget, estimate_tokens (80 lines)
│   ├── drift_watcher_seq005*         # DriftWatcher — file-size drift detection (103 lines)
│   ├── resistance_bridge_seq006*     # HesitationAnalyzer — telemetry→compiler (119 lines)
│   ├── streaming_layer_seq007*       # MONOLITH 1150 lines (intentional — compiler test input)
│   ├── operator_stats_seq008*        # OperatorStats — self-growing profile (394 lines)
│   ├── rework_detector_seq009*       # score_rework — AI answer quality scoring (106 lines)
│   ├── query_memory_seq010*          # record_query — recurring gap fingerprinting (118 lines)
│   ├── file_heat_map_seq011*         # update_heat_map — cognitive load per module (139 lines)
│   ├── operator_stats/               # Compiled package (14 files, pigeon-compliant)
│   └── cognitive/
│       ├── adapter_seq001*           # get_cognitive_modifier — 7 states → prompt/temp (125 lines)
│       ├── unsaid/                   # Compiled: unsaid thought reconstruction (9 files)
│       └── drift/                    # Compiled: cross-session drift detection (7 files)
│
├── streaming_layer/                  # Pigeon-compiled: 19 files, 100% compliant
│
├── pigeon_compiler/                  # The compiler (~62 modules, compiles itself)
│   ├── state_extractor/              # AST parsing, call graphs, import tracing, resistance scoring (6 modules)
│   ├── weakness_planner/             # DeepSeek cut plan generation (1 module)
│   ├── cut_executor/                 # Slicing, bin-packing, class decomposition (11 modules)
│   ├── rename_engine/                # Import rewriting, renames, self-healing (12 modules)
│   ├── runners/                      # Pipeline orchestrators + batch compiler (8 modules)
│   ├── integrations/                 # DeepSeek API adapter (1 module)
│   ├── bones/                        # Shared utilities (5 modules)
│   └── git_plugin.py                 # Post-commit daemon (the heart of the system)
│
├── vscode-extension/                 # VS Code extension: Pigeon Chat
│   ├── src/extension.ts              # PigeonChatPanel + classify bridge
│   ├── media/chat.html               # Chat UI with keystroke capture
│   ├── classify_bridge.py            # Python orchestrator (373 lines)
│   └── package.json
│
├── test_all.py                       # 4 core tests, zero deps
├── deep_test.py                      # 8 deep profiling E2E tests
├── pigeon_registry.json              # Module index: 85+ entries with token history
├── operator_profile.md               # Living cognitive profile (auto-updated every message)
├── operator_coaching.md              # DeepSeek-synthesized behavioral coaching (auto-updated)
├── rework_log.json                   # AI answer quality log (plain JSON array)
├── query_memory.json                 # Recurring query fingerprints + abandoned themes
├── file_heat_map.json                # Cognitive load per module
└── MASTER_MANIFEST.md                # Auto-generated project map (rebuilt on commit)
```

---

## Current Status

| Capability | Status | Module |
|---|---|---|
| Post-commit auto-rename + import rewrite | ✅ Live | `git_plugin.py` + `rename_engine/` |
| Prompt box injection on every commit | ✅ Live | `git_plugin._inject_box()` |
| Registry + session audit trail | ✅ Live | `pigeon_registry.json` + `logs/pigeon_sessions/` |
| MANIFEST.md rebuild on commit | ✅ Live | `rename_engine/manifest_builder_seq007*` |
| `copilot-instructions.md` auto-index rebuild | ✅ Live | `git_plugin._refresh_copilot_instructions()` |
| `copilot-instructions.md` operator state snapshot | ✅ Live | `classify_bridge._refresh_operator_state()` |
| Compiler: function decomposition (AST) | ✅ Live | `state_extractor/ast_parser_seq001*` |
| Compiler: class decomposition (DeepSeek) | ✅ Live | `cut_executor/func_decomposer_seq008*` |
| Compiler: batch codebase compile | ✅ Live | `runners/run_batch_compile_seq015*` |
| Cognitive state classification (7 states) | ✅ Live | `operator_stats_seq008*` |
| Unsaid thought reconstruction | ✅ Live | `cognitive/unsaid/` (9 files) |
| Cross-session drift detection | ✅ Live | `cognitive/drift/` (7 files) |
| Self-growing operator profile | ✅ Live | `operator_stats_seq008*` → `operator_profile.md` |
| Telemetry → compiler resistance signal | ✅ Live | `resistance_bridge_seq006*` |
| **Rework detector (AI miss scoring)** | ✅ Live | `rework_detector_seq009*` → `rework_log.json` |
| **Query memory (recurring gaps)** | ✅ Live | `query_memory_seq010*` → `query_memory.json` |
| **File heat map (cognitive load)** | ✅ Live | `file_heat_map_seq011*` → `file_heat_map.json` |
| **DeepSeek coaching synthesis** | ✅ Live | `classify_bridge._build_prompt()` + `git_plugin` |
| **Post-response event capture** | ✅ Live | `chat.html` (30s window) + `extension.ts` |
| VS Code extension (Pigeon Chat) | ✅ Live | `vscode-extension/` — F5 to launch |
| **Cognitive state → LLM call site wiring** | 🔄 Adapter exists, not yet wired | `cognitive/adapter_seq001*` |
| **`pigeon init` CLI** | 🔄 Hook installs manually today | `pyproject.toml` entry points |

---

## Quick Start

```bash
# Clone and test
git clone https://github.com/SavageCooPigeonX/keystroke-telemetry.git
cd keystroke-telemetry
pip install .
py test_all.py     # 4 core tests pass
py deep_test.py    # 8 deep profiling tests pass

# Launch VS Code extension
cd vscode-extension
npm install
npm run compile
# Press F5 → Extension Development Host
# Ctrl+Shift+P → "Pigeon: Open Keystroke-Aware Chat"

# Use Pigeon in your own repo:
pigeon init
```

**Requirements**:
| Component | Needs |
|---|---|
| Core telemetry + compiler | Python 3.10+ stdlib only, zero deps |
| Compiler DeepSeek flows | `httpx` (`pip install httpx`), `DEEPSEEK_API_KEY` env var |
| VS Code extension | Node.js 18+, `npm install` in `vscode-extension/` |
| Windows | Use `py` launcher, set `$env:PYTHONIOENCODING = "utf-8"` |

---

## License

MIT. See [`LICENSE`](LICENSE).
