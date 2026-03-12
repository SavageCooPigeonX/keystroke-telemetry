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

## What It Tracks

| Signal | How |
|---|---|
| **Typing speed** | `delta_ms` between inserts → WPM |
| **Typo correction** | Backspace bursts followed by re-typing |
| **Cognitive pauses** | `delta_ms > 2000` = the operator is thinking |
| **Discarded messages** | Started composing, then abandoned |
| **Paste + edit** | Pasted text then modified (prompt refinement) |
| **Hesitation score** | Per-message: `pause_ratio + deletion_ratio` (0.0–1.0) |

## Architecture

```
keystroke-telemetry/
├── src/
│   ├── timestamp_utils_seq001_v001.py   # ms-epoch utility
│   ├── models_seq002_v001.py            # KeyEvent + MessageDraft dataclasses
│   ├── logger_seq003_v001.py            # Core telemetry logger (v2 schema)
│   ├── context_budget_seq004_v001.py    # LLM-aware file sizing scorer
│   ├── drift_watcher_seq005_v001.py     # Live drift detection for coding loops
│   ├── resistance_bridge_seq006_v001.py # Telemetry → pigeon compiler signal
│   └── __init__.py
├── test_all.py                          # Full test suite
└── .gitignore
```

Every file has an `@pigeon` preamble:
```python
# @pigeon: seq=003 | role=core_logger | depends=[timestamp_utils,models] | exports=[TelemetryLogger] | tokens=~1800
```
An LLM agent reads only these lines to build a project map without parsing imports.

## Pigeon Compiler Integration

The **resistance bridge** connects keystroke telemetry to the [Pigeon Code Compiler](https://github.com/SavageCooPigeonX/pigeon-code-compiler):

```python
from src import HesitationAnalyzer

analyzer = HesitationAnalyzer(summary_dir="logs")
signal = analyzer.resistance_signal()
# → {"adjustment": 0.195, "reason": "high hesitation (0.428); high discard rate (0.333)"}
```

Files that cause the most human hesitation get a **resistance score bump** — they become split candidates. The compiler restructures code where *humans actually struggle*, not just where the AST says it's complex.

## Context Budget (vs. flat line count)

Instead of `PIGEON_MAX = 50`, files are scored by **LLM context cost**:

```
context_cost = file_tokens + (coupling_score × dependency_tokens)
```

- **Hard cap**: 88 lines (~2K tokens — fits 3–4 files in an agent's working memory)
- **Budget**: file + weighted dependencies ≤ 3000 tokens
- Self-contained files get a bonus; heavily-coupled files get pushed shorter

## Quick Start

```bash
git clone <this-repo>
cd keystroke-telemetry
py test_all.py
```

Zero dependencies. Python 3.11+ stdlib only.

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

## License

Proprietary. Contact SavageCooPigeonX for licensing.
