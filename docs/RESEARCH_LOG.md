# Research Log — The System Studying Us

*Auto-generated 2026-03-31 17:54 UTC by `research_lab_seq029`. This document is rewritten on every push. It contains what the prediction engine, self-fix scanner, and cognitive profiler have learned about human/AI pair programming.*

## 1. Prediction Engine — What It Gets Right and Wrong
**200 predictions scored** across 3 modes.

| Mode | N | Avg F1 | Hit Rate | Avg Calibration Error |
|------|---|--------|----------|-----------------------|
| failure | 67 | 0.000 | 0.0% | 0.374 |
| heat | 67 | 0.031 | 16.4% | 0.355 |
| targeted | 66 | 0.013 | 12.1% | 0.363 |

### The Fixation Problem

The predictor keeps guessing the same modules — the ones the operator *hesitates* on — not the ones they *actually edit*.

**Most over-predicted (false positives):**
- `file_heat_map` — predicted 179x, rarely edited
- `file_writer` — predicted 179x, rarely edited
- `import_rewriter` — predicted 179x, rarely edited
- `logger` — predicted 47x, rarely edited
- `models` — predicted 47x, rarely edited

**Actually edited (true hits):**
- `dynamic_prompt` — correctly predicted 10x
- `operator_stats` — correctly predicted 9x
- `cognitive_reactor` — correctly predicted 5x
- `cognitive_reactor_seq014_decision_maker` — correctly predicted 1x

**Interpretation:** Hesitation ≠ intent. The operator hesitates on scary/complex modules but edits familiar ones. The prediction engine confuses cognitive load with task selection. This is a fundamental insight about human/AI pair programming — the AI watches where you sweat, but you work where you're comfortable.

**24 predictions still unscored** (awaiting next push cycle).

## 2. Cognitive Patterns — What We Know About the Operator
- **Dominant state: focused**
- **Submit rate: 14/21 (66%)**

**Interpretation:** The operator deletes ~4.1% of what they type (from chat compositions). Dominant cognitive state: **focused**. 121 prompts recorded in prompt journal (submit rate: 66% of profiled messages). The system captures typing patterns, hesitation, and deleted words that would otherwise be invisible.

## 3. Pair Dynamics — How Human + AI Actually Collaborate

**Rework verdicts** (121 foreground responses scored):
- OK: 121 (100%) — copilot nailed it
- Partial: 0 (0%) — needed adjustment
- Miss: 0 (0%) — operator had to redo
- Data quality note: excluded 79 background rework entries (`bg:` queries)
- Data quality note: all non-background verdicts are currently `ok`, which suggests the miss signal is still incomplete or misrouted

**Prompt→file pairings:** 65 edits traced back to prompts.
- Filtered median prompt-to-edit latency: 235.7s
- Filtered average prompt-to-edit latency: 473.2s across 35 sane pairs
- Data quality note: 30 pairings had negative or outlier latencies and were excluded

**Prompt mutations:** 85 changes to copilot-instructions.md, scored against 200 rework pairs.
- No significant signal yet — all sections scored neutral.

**Cognitive reactor:** 179 fires. 0 code patches applied (0% acceptance).

**Shared memory shards** (10 active):
- `api_preferences`
- `architecture_decisions`
- `commit_patterns`
- `frustration_triggers`
- `module_pain_points`
- `module_relationships`
- `prompt_patterns`
- `success_patterns`

**Interpretation:** Copilot gets it right 100% of the time, misses 0%. The pair communicates through: keystrokes (operator→system), rework verdicts (operator→copilot quality signal), prompt mutations (system→copilot instruction tuning), reactor patches (copilot→codebase autonomous edits), and memory shards (shared context that persists across sessions). This is not one-way automation — it is a feedback loop where both sides adapt. The operator's typing patterns steer the AI's reasoning, and the AI's prompt mutations steer the operator's workflow. Neither side is fully in control.

## 4. Recursive Code Evolution — The Codebase Changing Itself

**41 self-fix reports** from 2026-03-16 to 2026-03-31.
- Early avg problems: 24
- Recent avg problems: 21
- Trend: **improving**

**10 push cycles** completed. Latest sync score: 0.55

**41 push narratives** — each file explains why it was touched, what assumption could break, and what regression to watch for.

**Interpretation:** The codebase rewrites its own module boundaries, catches its own stale imports, and compiles its own size violations. Each commit triggers: rename → self-fix scan → backward pass → prediction → coaching injection. The code evolves through its own diagnostic pipeline, not just through human edits.

## 5. Signal Quality — How Good Is Our Data
- **Rework log:** 200 entries. Last 20 unique scores: 1 ⚠️ (likely placeholder data)
- **Background rework noise:** 79/200 entries come from `bg:` queries and can distort answer-quality analysis
- **Training pairs:** 6 captured with muxed cognitive state
- **Memory shards:** 10 active (local markdown, zero LLM calls)

## 6. Open Research Questions

1. **Hesitation ≠ intent** — can we separate "thinking about X" from "about to edit X"?
2. **Deletion ratio as confidence** — does deletion ratio indicate uncertainty or refinement?
3. **Prediction calibration** — confidence is stuck at 0.49-0.50, needs dynamic update
4. **Cross-session memory** — do shard patterns persist across conversations?
5. **Rework signal** — is the 0.003 score a measurement or a default? Needs audit
6. **Recursive depth** — at what point does the system's self-modification change the operator's behavior? When does the observer change the observed?
