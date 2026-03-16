# Keystroke Telemetry + Pigeon Code Engine

Two tools, one goal: **make codebases self-documenting and LLM-readable by default.**

1. **Pigeon Code Engine** — drop it into any repo. From that point on, every commit autonomously refactors files to stay under 200 lines, renames them with living metadata, rewrites all imports, writes manifests, and injects prompt boxes. The human manages intent (via commit messages). The files track everything else.

2. **Keystroke Telemetry** — captures typing patterns in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, and feeds hesitation signals back into the compiler. Files that cause the most human friction get split more aggressively.

> Not a keylogger. Telemetry captures events **within your own app's text field** and runs locally.

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
  Auto-commits [pigeon-auto]
```

**What you provide**: intent (the commit message).  
**What the files provide**: description (from docstring), version history, token cost, mutation log.  
**What the compiler provides**: size enforcement, import consistency, LLM-readable output.

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
 1. Parse commit message → intent slug ("timeout_buffer_polling")
 2. For each changed pigeon .py file:
    · Read docstring → desc slug
    · Bump version, update date
    · Build import_map {old_module → new_module}
 3. Rewrite all imports across codebase  ← BEFORE renaming
 4. Rename files on disk
 5. Inject/update prompt boxes
 6. Log to logs/pigeon_sessions/{name}.jsonl
 7. Update pigeon_registry.json
 8. Rebuild all MANIFEST.md files
 9. Refresh .github/copilot-instructions.md auto-index
10. Refresh `.github/copilot-instructions.md` operator state snapshot
11. Auto-commit [pigeon-auto]
```

The import rewrite always happens *before* file rename — the codebase is never left in a broken import state.

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

Every file announces itself: seq, version, token cost, what it does, what changed last, how many times it's been touched.

### Naming convention

```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```

| Part | Meaning | Source |
|---|---|---|
| `name` | Module identity | Stable, never changes |
| `seq{NNN}` | Sequence within folder | Never changes |
| `v{NNN}` | Version | Auto-incremented on every touch |
| `d{MMDD}` | Date of last mutation | UTC today |
| `description` | What the file DOES | Extracted from docstring |
| `_lc_` | Lifecycle separator | Fixed |
| `intent` | What was LAST DONE | Commit message, 3 words |

**Critical**: never hardcode full pigeon filenames — they change on every commit. Search by `name_seqNNN*`.

### The compiler: oversized files get split automatically

When a file exceeds 200 lines, the compiler runs:

```
Oversized file (e.g. 394 lines)
   ↓
Phase 1  — AST decompose oversized functions (free, no LLM)
Phase 1b — Class decomposition via DeepSeek (~$0.001)
            (extracts methods as standalone functions, keeps class thin)
Phase 2  — DeepSeek generates a cut plan with exact line assignments
Phase 3  — Deterministic bin-packing → N files × ≤50 lines + __init__.py + MANIFEST.md
```

The compiler compiles itself — every module in `pigeon_compiler/` was split by running the compiler on its own source.

```bash
# Compile one file:
py -m pigeon_compiler.runners.run_clean_split_seq010* path/to/big_file.py

# Compile entire codebase:
py -m pigeon_compiler.runners.run_batch_compile_seq015* --dry-run
py -m pigeon_compiler.runners.run_batch_compile_seq015*
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

### Capture → Classify → Inject

```
Browser keystrokes
      ↓
  TelemetryLogger  →  hesitation_score, cognitive_state
      ↓
  get_cognitive_modifier(state)
      ↓
  { prompt_injection, temperature_modifier, strategy }
      ↓
  Inject into LLM system prompt + adjust temperature
```

Seven states classified from typing patterns alone — zero LLM calls:

| State | Signal | Prompt adaptation | Temp Δ |
|---|---|---|---|
| `frustrated` | Heavy deletions, restart loops | Concise, 2-3 options, bullets | −0.1 |
| `hesitant` | Long inter-key pauses, low WPM | Warm, anticipate intent, follow-up | +0.05 |
| `flow` | Fast typing, minimal edits | Match energy, full technical depth | +0.1 |
| `focused` | Steady, deliberate | Thorough, well-structured | 0 |
| `restructuring` | Heavy rewrite before submit | Precise, match effort | −0.05 |
| `abandoned` | Deleted message, re-approached | Welcoming, direct | 0 |
| `neutral` | Baseline | Standard | 0 |

### Browser capture

```javascript
KeystrokeTelemetry.attach('chat-input', {
    agentType: 'assistant',
    flushEndpoint: '/api/telemetry/keystrokes'
});

const result = await KeystrokeTelemetry.onSubmit('chat-input', finalText);
// → { cognitive_state: 'frustrated', hesitation_score: 0.62 }
```

Schema: `keystroke_telemetry/v2`. Auto-flushes at 200 events. Abandon detection at 30s blur. Paste tracking. Pause detection (>2s gaps).

### Unsaid thoughts reconstruction

Recovers what the operator typed and deleted:

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

### Cross-session drift detection

Detects frustration escalation, flow streaks, engagement decline against personal baseline:

```python
from src.cognitive.drift import detect_session_drift, build_cognitive_context

drift = detect_session_drift(session_summaries, baseline)
# → { frustration_escalating: True, engagement_trend: 'declining' }
```

### Self-growing operator profile

Written to `operator_profile.md` every 8 messages and **auto-injected into `.github/copilot-instructions.md`** on every pigeon commit:

```markdown
**Dominant: `hesitant`** | Submit: 66% | WPM: 47.8 | Del: 25.6% | Hes: 0.443

**Behavioral tunes for this session:**
- hesitant → warm tone, anticipate intent, ask one follow-up question
- WPM < 45 → prefer bullets and code blocks over dense prose
- Hesitation > 0.4 → proactively offer alternatives or examples
```

Copilot reads this at the start of every session — no manual context-setting required.

### Resistance bridge: telemetry feeds the compiler

Files that cause the most human hesitation get a resistance score bump — the compiler splits them more aggressively:

```python
from src.resistance_bridge import HesitationAnalyzer

signal = HesitationAnalyzer("logs").resistance_signal()
# → {"adjustment": 0.195, "reason": "high hesitation (0.428); high discard (0.333)"}
```

---

## Current Status

| Capability | Status |
|---|---|
| Post-commit auto-rename + import rewrite | ✅ Live |
| Prompt box injection on every commit | ✅ Live |
| Registry + session audit trail | ✅ Live |
| MANIFEST.md rebuild on commit | ✅ Live |
| `copilot-instructions.md` auto-index rebuild | ✅ Live |
| `copilot-instructions.md` operator state snapshot | ✅ Live |
| Compiler: function decomposition (AST) | ✅ Live |
| Compiler: class decomposition (DeepSeek) | ✅ Live |
| Compiler: batch codebase compile | ✅ Live |
| Cognitive state classification (7 states) | ✅ Live |
| Unsaid thought reconstruction | ✅ Live |
| Cross-session drift detection | ✅ Live |
| Self-growing operator profile | ✅ Live |
| Telemetry → compiler resistance signal | ✅ Live |
| **Cognitive state → LLM call site wiring** | 🔄 Adapter exists, not yet wired |
| **VS Code extension (Pigeon Chat)** | ✅ Live — F5 to launch |
| **`pigeon init` CLI** | 🔄 Hook installs manually today |

---

## Project Structure

```
keystroke-telemetry/
├── .github/
│   └── copilot-instructions.md    # Auto-updated LLM context (self-mutates on commit)
│
├── client/
│   └── keystroke-telemetry.js     # Browser IIFE: attach/onSubmit/getLastState
│
├── src/                           # Core telemetry + cognitive layer
│   ├── timestamp_utils_seq001*    # ms-epoch utility
│   ├── models_seq002*             # KeyEvent + MessageDraft dataclasses
│   ├── logger_seq003*             # Core logger, v2 schema
│   ├── context_budget_seq004*     # LLM-aware token cost scorer
│   ├── drift_watcher_seq005*      # File-size drift detection
│   ├── resistance_bridge_seq006*  # Telemetry → compiler hesitation signal
│   ├── streaming_layer_seq007*    # Monolith (intentional — compiler test input)
│   ├── operator_stats_seq008*     # Self-growing operator profile writer
│   ├── operator_stats/            # Compiled package (14 files, pigeon-compliant)
│   └── cognitive/
│       ├── adapter_seq001*        # 7 states → prompt injection + temp modifiers
│       ├── unsaid/                # Compiled: unsaid thought reconstruction (9 files)
│       └── drift/                 # Compiled: cross-session drift detection (7 files)
│
├── streaming_layer/               # Pigeon-compiled: 19 files, 100% compliant
│
├── pigeon_compiler/               # The compiler (~62 modules, compiles itself)
│   ├── state_extractor/           # AST parsing, call graphs, resistance scoring
│   ├── weakness_planner/          # DeepSeek cut plan generation
│   ├── cut_executor/              # Slicing, bin-packing, class decomposition
│   ├── rename_engine/             # Import rewriting, renames, self-healing
│   ├── runners/                   # Pipeline orchestrators + batch compiler
│   ├── integrations/              # DeepSeek API adapter
│   └── git_plugin.py              # Post-commit daemon (the heart of the system)
│
├── test_all.py                    # 4 tests, zero deps beyond stdlib
├── pigeon_registry.json           # Module index: seq, ver, date, tokens, history
├── operator_profile.md            # Living cognitive profile (auto-updated)
└── MASTER_MANIFEST.md             # Auto-generated project map
```

---

## VS Code Extension: Pigeon Chat

A custom chat panel with full keystroke telemetry embedded. **Closes the loop** — every message you type is classified and injected into the model's system context *before* it responds.

```
vscode-extension/
├── src/extension.ts       # panel + LM bridge (Copilot → DeepSeek fallback)
├── media/chat.html        # chat UI with inline keystroke capture
├── classify_bridge.py     # Python bridge → classify_state → operator_profile.md
├── package.json
└── tsconfig.json
```

### What runs on every message

```
User types in Pigeon Chat panel
  ↓ keydown/input events captured with timestamps
  ↓ on submit → classify_bridge.py receives events JSON
  ↓ computes: wpm, del_ratio, pause_ratio, hesitation_score
  ↓ classify_state() → one of 7 cognitive states
  ↓ OperatorStats.ingest() → updates operator_profile.md (every 8 msgs)
  ↓ _refresh_operator_state() → rewrites copilot-instructions.md IMMEDIATELY
  ↓ operator-state block read → prepended as system context to LM request
  ↓ response adapted to current cognitive state in real time
```

No git commit needed for the context update — writes direct to disk.

### Build

```bash
cd vscode-extension
npm install
npm run compile
# Then press F5 in VS Code → Extension Development Host opens
# Run command: "Pigeon: Open Keystroke-Aware Chat"
```

### Model priority

1. `vscode.lm` API — uses whatever Copilot model is active
2. DeepSeek fallback — set `DEEPSEEK_API_KEY` in env

---

## Quick Start

```bash
git clone https://github.com/SavageCooPigeonX/keystroke-telemetry.git
cd keystroke-telemetry
pip install .
py test_all.py   # all 4 pass

# To use Pigeon in your own repo:
pigeon init
```

**Core (telemetry + compiler)**: Python 3.10+ stdlib only, zero deps.  
**Compiler DeepSeek flows**: install `httpx`, set `DEEPSEEK_API_KEY`.  
**Windows**: use `py` launcher, set `$env:PYTHONIOENCODING = "utf-8"`.

---

## License

MIT. See [`LICENSE`](LICENSE).
