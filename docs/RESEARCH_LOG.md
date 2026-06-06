# What The System Knows Right Now

*Auto-generated 2026-06-05 23:51 UTC · 3 prompts · 1 rework entries · zero LLM calls*

> This report is rewritten on every push. Every prediction becomes pass/fail when the next push lands.
> All signals are measured from live telemetry — nothing is inferred or hallucinated.

## What Gets Touched Next

*200 scored predictions · zero LLM calls*


> **Prediction bias:** chronically over-predicts `file_heat_map`, `master_test`, `tc_intent_manager` — operator thinks about them more than they touch them

### Blind Spots *[source: measured]*
*Edited without being predicted — the real surprises:*
- `__init__` — 150x unpredicted
- `__main__` — 100x unpredicted
- `stress_test_architecture` — 50x unpredicted
- `tc_observatory` — 50x unpredicted
- `tc_sim` — 50x unpredicted

## Live Operator State

*3 prompts profiled · source: measured*

**Dominant: `focused` | Submit: 60%**

## Pair Performance

*1 responses scored · 0 background excluded*

**Accuracy: 0% OK | 0% miss** *[source: measured]*

### Mutation Effectiveness *[source: measured]*
*174 mutations scored*
- no significant signal yet — all sections scored neutral

## Codebase Health

*73 self-fix reports · 2026-03-16 → 2026-06-05*

**Problem trend: growing** (early avg 24 → recent avg 90) *[source: measured]*
- problems growing ~66/push — expect more over_hard_cap and dead_exports without intervention

## Unsaid Threads

*Deleted from prompts — operator wanted this but did not ask:*

- "flow"
- "only"
- "describe"
- "the"

## Confidence

*How much to trust this report:*

- **Rework signal:** WEAK (placeholder data) — 1 entries, 1 unique scores in last 20
- **Prediction accuracy:** F1=0.014, calibration=0.158 (200 scored)
  - predictions near-random — treat all forecasts as hypotheses

### Hypotheses Under Test
*These predictions become pass/fail on next push:*

1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited
2. **Deletion trend predicts mode** — rising deletion → restructuring, not building
3. **Rework trajectory holds** — if improving, fewer misses next push
4. **Self-fix converging** — if problem count falling, fewer violations next push
5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated
