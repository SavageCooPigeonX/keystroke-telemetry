# Research Log — The System Studying Us

*Auto-generated 2026-03-31 14:53 UTC by `research_lab_seq029`. This document is rewritten on every push. It contains what the prediction engine, self-fix scanner, and cognitive profiler have learned about human/AI pair programming.*

## 1. Prediction Engine — What It Gets Right and Wrong
**200 predictions scored** across 3 modes.

| Mode | N | Avg F1 | Hit Rate | Avg Calibration Error |
|------|---|--------|----------|-----------------------|
| failure | 67 | 0.000 | 0.0% | 0.448 |
| heat | 67 | 0.018 | 16.4% | 0.437 |
| targeted | 66 | 0.030 | 24.2% | 0.428 |

### The Fixation Problem

The predictor keeps guessing the same modules — the ones the operator *hesitates* on — not the ones they *actually edit*.

**Most over-predicted (false positives):**
- `file_heat_map` — predicted 197x, rarely edited
- `file_writer` — predicted 197x, rarely edited
- `import_rewriter` — predicted 197x, rarely edited
- `logger` — predicted 62x, rarely edited
- `models` — predicted 62x, rarely edited

**Actually edited (true hits):**
- `push_narrative` — correctly predicted 9x
- `operator_stats` — correctly predicted 9x
- `dynamic_prompt` — correctly predicted 5x
- `cognitive_reactor` — correctly predicted 4x

**Interpretation:** Hesitation ≠ intent. The operator hesitates on scary/complex modules but edits familiar ones. The prediction engine confuses cognitive load with task selection. This is a fundamental insight about human/AI pair programming — the AI watches where you sweat, but you work where you're comfortable.

**18 predictions still unscored** (awaiting next push cycle).

## 2. Cognitive Patterns — What We Know About the Operator

**Interpretation:** The operator deletes ~3.7% of what they type (from chat compositions). Dominant cognitive state: **unknown**. 111 real chat submits recorded in prompt journal. The system captures typing patterns, hesitation, and deleted words that would otherwise be invisible.

## 3. Recursive Code Evolution — The Codebase Changing Itself

**39 self-fix reports** from 2026-03-16 to 2026-03-31.
- Early avg problems: 24
- Recent avg problems: 21
- Trend: **improving**

**8 push cycles** completed. Latest sync score: 0.327

**39 push narratives** — each file explains why it was touched, what assumption could break, and what regression to watch for.

**Interpretation:** The codebase rewrites its own module boundaries, catches its own stale imports, and compiles its own size violations. Each commit triggers: rename → self-fix scan → backward pass → prediction → coaching injection. The code evolves through its own diagnostic pipeline, not just through human edits.

## 4. Signal Quality — How Good Is Our Data
- **Rework log:** 200 entries. Last 20 unique scores: 1 ⚠️ (likely placeholder data)
- **Training pairs:** 5 captured with muxed cognitive state
- **Memory shards:** 8 active (local markdown, zero LLM calls)

## 5. Open Research Questions

1. **Hesitation ≠ intent** — can we separate "thinking about X" from "about to edit X"?
2. **Deletion ratio as confidence** — does deletion ratio indicate uncertainty or refinement?
3. **Prediction calibration** — confidence is stuck at 0.49-0.50, needs dynamic update
4. **Cross-session memory** — do shard patterns persist across conversations?
5. **Rework signal** — is the 0.003 score a measurement or a default? Needs audit
6. **Recursive depth** — at what point does the system's self-modification change the operator's behavior? When does the observer change the observed?
