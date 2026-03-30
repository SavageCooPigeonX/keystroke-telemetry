# Research Log — The System Studying Us

*Auto-generated 2026-03-30 22:18 UTC by `research_lab_seq029`. This document is rewritten on every push. It contains what the prediction engine, self-fix scanner, and cognitive profiler have learned about human/AI pair programming.*

## 1. Prediction Engine — What It Gets Right and Wrong
**200 predictions scored** across 3 modes.

| Mode | N | Avg F1 | Hit Rate | Avg Calibration Error |
|------|---|--------|----------|-----------------------|
| failure | 67 | 0.000 | 0.0% | 0.532 |
| heat | 67 | 0.012 | 10.4% | 0.525 |
| targeted | 66 | 0.031 | 21.2% | 0.513 |

### The Fixation Problem

The predictor keeps guessing the same modules — the ones the operator *hesitates* on — not the ones they *actually edit*.

**Most over-predicted (false positives):**
- `file_heat_map` — predicted 200x, rarely edited
- `file_writer` — predicted 200x, rarely edited
- `import_rewriter` — predicted 200x, rarely edited
- `logger` — predicted 80x, rarely edited
- `models` — predicted 80x, rarely edited

**Actually edited (true hits):**
- `push_narrative` — correctly predicted 16x
- `cognitive_reactor` — correctly predicted 5x

**Interpretation:** Hesitation ≠ intent. The operator hesitates on scary/complex modules but edits familiar ones. The prediction engine confuses cognitive load with task selection. This is a fundamental insight about human/AI pair programming — the AI watches where you sweat, but you work where you're comfortable.

**9 predictions still unscored** (awaiting next push cycle).

## 2. Cognitive Patterns — What We Know About the Operator
- **Dominant state: frustrated**
- **Submit rate: 227/6382 (3%)**
- Longest struggle streak: **724 messages** in a row (afternoon). Consider a break.

**Interpretation:** The operator deletes ~47% of what they type. They are frustrated 48% of the time and hesitant 31%. Only 3% of messages are submitted — 97% are abandoned drafts. The system captures the 97% that would otherwise be invisible.

## 3. Recursive Code Evolution — The Codebase Changing Itself

**36 self-fix reports** from 2026-03-16 to 2026-03-30.
- Early avg problems: 24
- Recent avg problems: 19
- Trend: **improving**

**5 push cycles** completed. Latest sync score: 0.7

**36 push narratives** — each file explains why it was touched, what assumption could break, and what regression to watch for.

**Interpretation:** The codebase rewrites its own module boundaries, catches its own stale imports, and compiles its own size violations. Each commit triggers: rename → self-fix scan → backward pass → prediction → coaching injection. The code evolves through its own diagnostic pipeline, not just through human edits.

## 4. Signal Quality — How Good Is Our Data
- **Rework log:** 200 entries. Last 20 unique scores: 1 ⚠️ (likely placeholder data)
- **Training pairs:** 2 captured with muxed cognitive state
- **Memory shards:** 8 active (local markdown, zero LLM calls)

## 5. Open Research Questions

1. **Hesitation ≠ intent** — can we separate "thinking about X" from "about to edit X"?
2. **Deletion ratio as confidence** — does 47% deletion mean uncertainty or refinement?
3. **Prediction calibration** — confidence is stuck at 0.49-0.50, needs dynamic update
4. **Cross-session memory** — do shard patterns persist across conversations?
5. **Rework signal** — is the 0.003 score a measurement or a default? Needs audit
6. **Recursive depth** — at what point does the system's self-modification change the operator's behavior? When does the observer change the observed?
