# Keystroke Telemetry for LLM Interfaces

**Cognitive-sync keystroke logger that captures typing patterns in LLM chat interfaces — typos, deletions, rewrites, pauses, discarded messages — and feeds hesitation signals back into code-aware tooling.**

> Not a keylogger. This captures input events **within your own app's text field** for operator pattern analysis.

---

## What It Does

Every keystroke in an LLM chat input emits a self-contained JSON block:

```json
{
  "schema": "keystroke_telemetry/v2",
  "seq": 14,
  "session_id": "1d91b3621b5d",
  "message_id": "96d6ce6605",
  "timestamp_ms": 1773280927585,
  "delta_ms": 42,
  "event_type": "insert",
  "key": "w",
  "cursor_pos": 6,
  "buffer": "Helo w",
  "buffer_len": 6
}
```

Each block is:
- **Self-contained** — no context needed to parse it
- **LLM-ingestible** — an agent can read the stream and reason about operator behavior
- **Millisecond-timestamped** — epoch ms, monotonically increasing

---

## What It Tracks

| Signal | How |
|---|---|
| **Typing speed** | `delta_ms` between inserts → WPM |
| **Typo correction** | Backspace bursts followed by re-typing |
| **Cognitive pauses** | `delta_ms > 2000` = the operator is thinking |
| **Discarded messages** | Started composing, then abandoned |
| **Paste + edit** | Pasted text then modified (prompt refinement) |
| **Hesitation score** | Per-message: `pause_ratio + deletion_ratio` (0.0–1.0) |

---

## Architecture

```
keystroke-telemetry/
├── src/                                    # Core telemetry library
│   ├── timestamp_utils_seq001_v001.py      #   ms-epoch utility (5 lines)
│   ├── models_seq002_v001.py               #   KeyEvent + MessageDraft dataclasses (31 lines)
│   ├── logger_seq003_v001.py               #   Core telemetry logger, v2 schema (143 lines)
│   ├── context_budget_seq004_v001.py       #   LLM-aware file sizing scorer (80 lines)
│   ├── drift_watcher_seq005_v001.py        #   Live drift detection for coding loops (95 lines)
│   ├── resistance_bridge_seq006_v001.py    #   Telemetry → pigeon compiler signal (111 lines)
│   ├── streaming_layer_seq007_v001.py      #   956-line monolith (compiler test input)
│   └── __init__.py
│
├── streaming_layer/                        # Pigeon-compiled output (20 files)
│   ├── streaming_layer_constants_seq001_v001.py
│   ├── streaming_layer_stream_client_seq002_v001.py
│   ├── streaming_layer_dataclasses_seq004-006_v001.py
│   ├── streaming_layer_formatter_seq004_v001.py
│   ├── streaming_layer_connection_pool_seq005_v001.py
│   ├── streaming_layer_aggregator_seq006_v001.py
│   ├── streaming_layer_metrics_seq007_v001.py
│   ├── streaming_layer_alerts_seq008_v001.py
│   ├── streaming_layer_replay_seq009_v001.py
│   ├── streaming_layer_dashboard_seq010_v001.py
│   ├── streaming_layer_http_handler_seq011_v001.py
│   ├── streaming_layer_orchestrator_seq016-017_v001.py
│   ├── streaming_layer_demo_*_v001.py      #   Demo/simulation helpers
│   ├── __init__.py
│   └── MANIFEST.md                         #   Prompt box + structure + changelog
│
├── pigeon_compiler/                        # The compiler itself (bugfixed)
│   ├── state_extractor/                    #   Layer 1: AST parsing, call graphs, resistance
│   ├── weakness_planner/                   #   Layer 2: DeepSeek cut plan generation
│   ├── cut_executor/                       #   Layer 3: Slicing, writing, bin-packing, resplit
│   ├── runners/                            #   Pipeline orchestrators
│   ├── integrations/                       #   DeepSeek API adapter
│   ├── bones/                              #   Shared utilities
│   ├── docs/                               #   Compiler design docs
│   └── output/                             #   Cached ether maps + plans
│
├── test_all.py                             # Full test suite (221 lines, 4 tests)
├── test_logs/                              # Test session output
├── demo_logs/                              # Demo session output
└── MASTER_MANIFEST.md                      # Project manifest + development plan
```

Every source file has an `@pigeon` preamble:
```python
# @pigeon: seq=003 | role=core_logger | depends=[timestamp_utils,models] | exports=[TelemetryLogger] | tokens=~1800
```
An LLM agent reads only these lines to build a project map without parsing imports.

---

## Pigeon Compiler Integration

The **resistance bridge** connects keystroke telemetry to the Pigeon Code Compiler:

```python
from src import HesitationAnalyzer

analyzer = HesitationAnalyzer(summary_dir="logs")
signal = analyzer.resistance_signal()
# → {"adjustment": 0.195, "reason": "high hesitation (0.428); high discard rate (0.333)"}
```

Files that cause the most human hesitation get a **resistance score bump** — they become split candidates. The compiler restructures code where *humans actually struggle*, not just where the AST says it's complex.

### Running the compiler

```powershell
$env:DEEPSEEK_API_KEY = "your-key"
py -c "
import sys; sys.path.insert(0, r'C:\Users\Nikita\Desktop')
from pigeon_compiler.runners.run_clean_split_seq010_v001 import run
from pathlib import Path
run(Path('src/streaming_layer_seq007_v001.py'), 'streaming_layer')
"
```

Pipeline phases:
1. **Decompose** — oversized functions split into ≤30-line sub-functions (free, AST only)
2. **Cut Plan** — DeepSeek generates a file-split plan with line count math (~$0.002)
3. **File Creation** — source slicer extracts functions, classes, constants by name
4. **Resplit Loop** — deterministic bin-packing until all non-class files ≤50 lines
5. **Init + Manifest** — `__init__.py` with re-exports, `MANIFEST.md` with prompt box
6. **Master Manifest** — updates project-level manifest with compilation record

---

## Context Budget (vs. flat line count)

Instead of `PIGEON_MAX = 50`, files are scored by **LLM context cost**:

```
context_cost = file_tokens + (coupling_score × dependency_tokens)
```

- **Hard cap**: 88 lines (~2K tokens — fits 3–4 files in an agent's working memory)
- **Budget**: file + weighted dependencies ≤ 3000 tokens
- Self-contained files get a bonus; heavily-coupled files get pushed shorter

---

## Quick Start

```bash
git clone <this-repo>
cd keystroke-telemetry
py test_all.py
```

Zero external dependencies. Python 3.11+ stdlib only.

(Pigeon compiler requires `httpx` for DeepSeek API calls.)

---

## Operator Profile (from ≥3 sessions)

```json
{
  "total_sessions": 5,
  "total_messages": 18,
  "avg_wpm": 62.3,
  "avg_hesitation_score": 0.31,
  "discard_rate": 0.22,
  "deletion_ratio": 0.18,
  "profile_confidence": "medium"
}
```

~100 event blocks across 3–5 turns is enough to start fingerprinting operator patterns with persistent state.

---

## License

Proprietary. Contact SavageCooPigeonX for licensing.
