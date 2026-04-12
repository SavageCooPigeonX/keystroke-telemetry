# What The System Knows Right Now

*Auto-generated 2026-04-11 15:29 UTC · 497 prompts · 200 rework entries · zero LLM calls*

> This report is rewritten on every push. Every prediction becomes pass/fail when the next push lands.
> All signals are measured from live telemetry — nothing is inferred or hallucinated.

## What Gets Touched Next

*200 scored predictions · zero LLM calls*


> **Prediction bias:** chronically over-predicts `file_heat_map`, `file_writer`, `import_rewriter` — operator thinks about them more than they touch them

### Blind Spots *[source: measured]*
*Edited without being predicted — the real surprises:*
- `classify_bridge` — 100x unpredicted
- `research_lab` — 97x unpredicted
- `cognitive_reactor_seq014_patch_writer` — 50x unpredicted
- `chat_response_reader` — 50x unpredicted
- `copilot_prompt_manager_seq020_orchestrator` — 50x unpredicted

## Live Operator State

*497 prompts profiled · source: measured*

**Dominant: `abandoned` | Submit: 66% | Del: 6.2%**
- operator entering flow state — productive building, less backtracking

## Pair Performance

*200 responses scored · 200 background excluded*

**Accuracy: 96% OK | 4% miss** *[source: measured]*
- trend: **degrading** (early 100% → recent 92%)
- quality slipping — check if prompt mutations are helping or hurting

**Prompt→edit latency:** 717.2s median (64 pairs)

### Mutation Effectiveness *[source: measured]*
*122 mutations scored*
- no significant signal yet — all sections scored neutral

**Reactor:** 524 fires, 0 accepted (0%)
> **Directive:** Reactor patches near-zero acceptance — tune confidence threshold or disable

## Codebase Health

*55 self-fix reports · 2026-03-16 → 2026-04-10*

**Problem trend: growing** (early avg 24 → recent avg 325) *[source: measured]*
- problems growing ~301/push — expect more over_hard_cap and dead_exports without intervention

### Fragile Contracts *[source: llm_derived]*
*From push narratives — treat as hypothesis:*
- REGRESSION WATCHLIST: Rename manifest validation silently passing corrupt maps; import rewrite missing symlinked files; prompt pre-processor mangling YAML instruction blocks.
- REGRESSION WATCHLIST: (1) predictor.get_surface_tensor shape contract change, (2) node_memory key `'numeric_surface'` missing or None, (3) surface object

### Recent Deaths *[source: measured]*
- `exception`: 3
- `loop`: 3
- `timeout`: 2
- `stale_import`: 2
> **Prediction:** `exception` remains dominant failure mode until root cause is addressed

### Electron Killers *[source: measured]*
- `graph_heat_map` — 2 deaths/4 calls (50%)

## Unsaid Threads

*Deleted from prompts — operator wanted this but did not ask:*

- "(ey"
- "ld f"
- "leaks _"
- "lready have this ;e"
- "e e"
- "ads/ use this to write  emaili litte"
- "opilot"
- "ggoooo"
- "es i"
- "7)$"

## Confidence

*How much to trust this report:*

- **Rework signal:** GOOD — 200 entries, 3 unique scores in last 20, 200 bg noise
- **Training pairs:** 125 captured
- **Prediction accuracy:** F1=0.010, calibration=0.305 (200 scored)
  - predictions near-random — treat all forecasts as hypotheses
- **Memory shards:** 11 active (zero LLM calls)

### Hypotheses Under Test
*These predictions become pass/fail on next push:*

1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited
2. **Deletion trend predicts mode** — rising deletion → restructuring, not building
3. **Rework trajectory holds** — if improving, fewer misses next push
4. **Self-fix converging** — if problem count falling, fewer violations next push
5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated
