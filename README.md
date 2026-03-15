# Keystroke Telemetry + Pigeon Code Engine

Two developer tools packaged together:

1. **Keystroke Telemetry** — captures typing patterns in LLM chat interfaces (pauses, deletions, rewrites, abandoned drafts) and classifies operator cognitive state in real time.
2. **Pigeon Code Engine** — self-documenting codebase engine. Filenames mutate on every commit to carry intent, description, version, and token metadata. The filename IS the changelog.

> Not a keylogger. Telemetry captures input events **within your own app's text field** and runs locally.

---

## Quick Start — Pigeon Code

```bash
# Install from a source checkout
pip install .

# Contributor workflow
pip install -e .

# Initialize in any git repo
cd your-project
pigeon init       # installs git hooks
pigeon status     # see codebase health
pigeon heal       # bulk inject prompt boxes + rebuild manifests
pigeon sessions   # view mutation audit trail
```

If you plan to use DeepSeek-backed compiler flows, install `httpx`, then copy `.env.example` to `.env` or export `DEEPSEEK_API_KEY` in your shell before running Layer 2 commands.

After `pigeon init`, every commit auto-renames touched pigeon files:

```bash
git commit -m "fix: timeout on buffer polling"
# → conversation_buffer_seq001_v005_d0316__buffer_polling_lc_timeout_buffer_polling.py
#   ├─ buffer_polling              = what the file DOES  (from docstring)
#   └─ timeout_buffer_polling      = what was LAST DONE  (from commit message)
```

### What happens on every commit

1. **Pre-commit** — advisory audit (never blocks): flags oversize files, missing versions
2. **Post-commit** — auto-rename daemon:
   - Parses commit message → 3-word intent slug
   - Reads docstring → desc slug
   - Bumps version + date
   - Renames file on disk
   - Injects prompt box header into file
   - Rewrites all imports across codebase
   - Logs session to `logs/pigeon_sessions/{name}.jsonl`
   - Updates `pigeon_registry.json`
   - Rebuilds all `MANIFEST.md` files
   - Auto-commits `[pigeon-auto]`

### Prompt Box (injected after docstring)

```python
# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v004 | 85 lines | ~2,100 tokens
# DESC:   filter_live_noise
# INTENT: fixed_timeout
# LAST:   2026-03-16 @ a3f2b1c
# SESSIONS: 4
# ──────────────────────────────────────────────
```

### Session Log (`logs/pigeon_sessions/noise_filter_seq007.jsonl`)

```jsonl
{"ts":"2026-03-16T14:32:01Z","hash":"a3f2b1c","msg":"fix: timeout on buffer polling","intent":"fixed_timeout","ver_before":3,"ver_after":4,"tokens_before":2050,"tokens_after":2100,"diff":"+12 -3"}
```

### Pigeon Code Naming Convention

```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```

| Part | Meaning | Source |
|---|---|---|
| `name` | Module identity | Stable, never changes |
| `seq{NNN}` | Sequence within folder | Set at creation |
| `v{NNN}` | Version (bumps every commit) | Auto-incremented |
| `d{MMDD}` | Date of last mutation | UTC today |
| `description` | What the file DOES | Extracted from docstring |
| `_lc_` | Separator (lifecycle) | Fixed |
| `intent` | What was LAST DONE | From commit message (3 words max) |

### CLI Commands

| Command | What it does |
|---|---|
| `pigeon init` | Install git hooks, create registry + session dir |
| `pigeon status` | Files, tokens, stale count, hook status, session count |
| `pigeon heal` | Bulk inject prompt boxes + token counts into all files |
| `pigeon sessions` | Show recent mutation logs across all files |
| `pigeon uninstall` | Remove hooks (preserve registry + logs) |

### Token Savings

On a 400-file codebase (~1.5M tokens):
- **10K-35K tokens saved per LLM session** (less file-opening, less re-discovery)
- **200K-700K tokens/day** at 20 sessions/day
- **$15-$150/month** in API cost reduction depending on model

---

## Keystroke Telemetry

### Browser Capture (JavaScript)

Drop `client/keystroke-telemetry.js` into any page:

```javascript
KeystrokeTelemetry.attach('chat-input', {
    agentType: 'assistant',
    flushEndpoint: '/api/telemetry/keystrokes'
});

// On message submit:
const result = await KeystrokeTelemetry.onSubmit('chat-input', finalText);
// result → { cognitive_state: 'frustrated', hesitation_score: 0.62 }
```

For public deployment, point `flushEndpoint` at a same-origin HTTPS route protected by your application's existing auth/session layer.

Every keystroke emits a `keystroke_telemetry/v2` JSON event with millisecond timing, cursor position, and buffer state. Events batch automatically (flush at 200 or on submit). Abandoned messages (30s blur timeout) are captured as `discard` events.

### Server Processing (Python)

```python
from src import TelemetryLogger

logger = TelemetryLogger(log_dir="logs")
result = logger.process_batch(events, final_text="How do I fix this?")
# result → { wpm: 43, hesitation: 0.38, state: 'hesitant', deletions: 12 }
```

### Cognitive State Classification

Seven states detected from typing patterns alone — no LLM calls:

| State | Typing Signal | Temperature Mod |
|---|---|---|
| `frustrated` | Fast deletions, restart loops | -0.1 (be concise) |
| `hesitant` | Long pauses before typing | +0.05 (be warm) |
| `flow` | Steady fast typing, minimal edits | +0.1 (match energy) |
| `focused` | Deliberate, measured, few pauses | 0 (thorough) |
| `restructuring` | Heavy cursor movement, reordering | -0.05 (precision) |
| `abandoned` | Started then left | 0 (welcoming return) |
| `neutral` | Baseline typing | 0 (no-op) |

```python
from src import get_cognitive_modifier

mod = get_cognitive_modifier('frustrated')
# mod → {
#   'prompt_injection': 'The operator is frustrated. Be concise...',
#   'temperature_modifier': -0.1,
#   'strategy': 'concise_direct'
# }
```

### Unsaid Thoughts Reconstruction

Recovers what operators typed and deleted — abandoned drafts, emotional deletions, topic pivots:

```python
from src import extract_unsaid_thoughts

unsaid = extract_unsaid_thoughts(keystroke_events, final_text)
# unsaid → {
#   'abandoned_drafts': ['I already tried that...'],
#   'emotional_deletions': [{'text': 'this is ridiculous', 'emotion': 'frustration'}],
#   'topic_pivots': 2,
#   'confidence': 0.74
# }
```

### Drift Detection

Compares current session to operator baseline — detects frustration escalation, flow streaks, engagement decline:

```python
from src import detect_session_drift, build_cognitive_context

drift = detect_session_drift(session_summaries, baseline)
# drift → { frustration_escalating: True, engagement_trend: 'declining' }

context = build_cognitive_context(operator_id, session_data)
# context → { cognitive_block: '...', adaptation_flags: ['FRUSTRATION_ESCALATING'] }
```

### Self-Growing Operator Profile

The logger silently writes `operator_profile.md` every 8 messages — accumulates real stats with LLM-readable observations:

```markdown
## Ranges
| Metric     | Min  | Max  | Avg  |
| WPM        | 18   | 95   | 50   |
| Hesitation | 0.03 | 0.62 | 0.27 |

## Time-of-Day Profile
| morning   | 4 msgs | 46 WPM | hesitant → focused |
| afternoon | 3 msgs | 83 WPM | flow               |
| night     | 2 msgs | 20 WPM | frustrated          |

## Patterns
- Morning warmup: early messages ~2.4x slower
- Late-night degradation: hesitation jumps from 0.307 to 0.550
```

---

## Pigeon Code Compiler

Autonomous code decomposition and naming engine. Takes oversized Python files and produces LLM-readable modules with structured filenames.

### Pigeon Code Naming Convention

```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```

Every source file carries an `@pigeon` preamble:
```python
# @pigeon: seq=003 | role=core_logger | depends=[timestamp_utils,models] | exports=[TelemetryLogger] | tokens=~1800
```
An LLM agent reads only these preambles to build a project map without parsing imports.

### Compiler Pipeline

```
Source File (956 lines)
  → State Extractor: AST parse, call graph, import trace, resistance score
  → Weakness Planner: DeepSeek generates cut plan (~$0.002)
  → Cut Executor: slice, write, bin-pack, resplit
  → Output: 20 files × ≤50 lines each, __init__.py, MANIFEST.md
```

1. **Decompose** — oversized functions split into ≤30-line sub-functions (free, AST only)
2. **Cut Plan** — DeepSeek generates a file-split plan with line count math
3. **File Creation** — source slicer extracts functions, classes, constants by name
4. **Resplit Loop** — deterministic bin-packing until all non-class files ≤50 lines
5. **Init + Manifest** — `__init__.py` with re-exports, `MANIFEST.md` with prompt box
6. **Master Manifest** — updates project-level manifest with compilation record

### Rename Engine

Autonomous rename pipeline with rollback:

1. **Scanner** — walks the project tree, identifies non-compliant files
2. **Planner** — generates rename plan with new pigeon-code names
3. **Import Rewriter** — rewrites all imports across the project
4. **Executor** — applies renames with atomic rollback on failure
5. **Validator** — post-rename import validation
6. **Self-Healer** — detects broken imports and auto-fixes

### Resistance Bridge (Telemetry → Compiler)

The bridge connects both tools — files that cause the most human hesitation get a resistance score bump and become split candidates:

```python
from src import HesitationAnalyzer

analyzer = HesitationAnalyzer(summary_dir="logs")
signal = analyzer.resistance_signal()
# → {"adjustment": 0.195, "reason": "high hesitation (0.428); high discard rate (0.333)"}
```

The compiler restructures code where *humans actually struggle*, not just where the AST says it's complex.

### Context Budget

Files scored by LLM context cost, not flat line count:

```
context_cost = file_tokens + (coupling_score × dependency_tokens)
```

- **Hard cap**: 88 lines (~2K tokens — fits 3–4 files in agent working memory)
- **Budget**: file + weighted dependencies ≤ 3000 tokens
- Self-contained files get a bonus; heavily-coupled files get pushed shorter

---

## Project Structure

```
keystroke-telemetry/
├── client/                                 # Browser capture layer
│   └── keystroke-telemetry.js              #   v2 IIFE, attach/onSubmit/getLastState
│
├── src/                                    # Core telemetry library
│   ├── timestamp_utils_seq001_v*_d*__*.py  #   ms-epoch utility
│   ├── models_seq002_v*_d*__*.py           #   KeyEvent + MessageDraft dataclasses
│   ├── logger_seq003_v*_d*__*.py           #   Core telemetry logger, v2 schema
│   ├── context_budget_seq004_v*_d*__*.py   #   LLM-aware file sizing scorer
│   ├── drift_watcher_seq005_v*_d*__*.py    #   Live drift detection for coding loops
│   ├── resistance_bridge_seq006_v*_d*__*.py#   Telemetry → pigeon compiler signal
│   ├── streaming_layer_seq007_v*_d*__*.py  #   Compiler test input monolith
│   ├── operator_stats_seq008_v*_d*__*.py   #   Self-growing operator profile
│   ├── cognitive/                          #   Cognitive intelligence layer
│   │   ├── adapter_seq001_v*_d*__*.py      #     7 states → prompt injection + temp modifiers
│   │   ├── unsaid_seq002_v*_d*__*.py       #     Reconstruct deleted/abandoned text
│   │   └── drift_seq003_v*_d*__*.py        #     Cross-session drift detection + baselines
│   └── __init__.py                         #   Package root (all exports)
│
├── streaming_layer/                        # Pigeon-compiled output (20 files)
│   ├── streaming_layer_*_v*_d*__*.py       #   Constants, connection pool, aggregator, etc.
│   ├── __init__.py
│   └── MANIFEST.md
│
├── pigeon_compiler/                        # Autonomous code decomposition engine
│   ├── state_extractor/                    #   Layer 1: AST parsing, call graphs, resistance
│   ├── weakness_planner/                   #   Layer 2: DeepSeek cut plan generation
│   ├── cut_executor/                       #   Layer 3: Slicing, writing, bin-packing, resplit
│   ├── rename_engine/                      #   Autonomous renames with rollback + self-heal
│   ├── runners/                            #   Pipeline orchestrators
│   ├── integrations/                       #   DeepSeek API adapter
│   └── docs/                               #   Compiler design documentation
│
├── test_all.py                             # Full test suite
├── stress_test.py                          # Cognitive stress test (5 scenarios)
└── MASTER_MANIFEST.md                      # Project manifest
```

---

## Quick Start

```bash
git clone https://github.com/SavageCooPigeonX/keystroke-telemetry.git
cd keystroke-telemetry
pip install .
python test_all.py
python test_public_release.py
```

**Telemetry**: Zero external dependencies. Python 3.10+ stdlib only.

**Pigeon Compiler**: Install `httpx` and provide `DEEPSEEK_API_KEY` (for example via `.env.example`) before using DeepSeek-backed commands.

---

## License

Released under the MIT License. See [`LICENSE`](LICENSE).
