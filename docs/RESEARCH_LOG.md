# What The System Knows Right Now

*Auto-generated 2026-04-03 01:56 UTC · 280 prompts · 200 rework entries · zero LLM calls*

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

*280 prompts profiled · source: measured*

**Dominant: `abandoned` | Submit: 66% | Del: 5.3%**
- operator entering restructuring mode — expect more deletions than new code

## Pair Performance

*57 responses scored · 143 background excluded*

**Accuracy: 100% OK | 0% miss** *[source: measured]*
- trend: **stable** (100% → 100%)

**Prompt→edit latency:** 365.4s median (48 pairs)

### Mutation Effectiveness *[source: measured]*
*106 mutations scored*
- no significant signal yet — all sections scored neutral

**Reactor:** 232 fires, 0 accepted (0%)
> **Directive:** Reactor patches near-zero acceptance — tune confidence threshold or disable

## Codebase Health

*48 self-fix reports · 2026-03-16 → 2026-04-02*

**Problem trend: growing** (early avg 24 → recent avg 441) *[source: measured]*
- problems growing ~417/push — expect more over_hard_cap and dead_exports without intervention

### Fragile Contracts *[source: llm_derived]*
*From push narratives — treat as hypothesis:*
- REGRESSION WATCHLIST: Regex pattern overfitting on extensions; missing dependency on external pattern configuration; silent pass on empty pattern list.

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

- "wor"
- "wouldn"
- "yiu gonna sa"
- "whats"
- "o please continue s"
- "test"
- "hts th"
- "tays"
- "cop"
- "rephraser"

## Confidence

*How much to trust this report:*

- **Rework signal:** GOOD — 200 entries, 3 unique scores in last 20, 143 bg noise
- **Training pairs:** 54 captured
- **Prediction accuracy:** F1=0.010, calibration=0.305 (200 scored)
  - predictions near-random — treat all forecasts as hypotheses
- **Memory shards:** 10 active (zero LLM calls)

### Hypotheses Under Test
*These predictions become pass/fail on next push:*

1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited
2. **Deletion trend predicts mode** — rising deletion → restructuring, not building
3. **Rework trajectory holds** — if improving, fewer misses next push
4. **Self-fix converging** — if problem count falling, fewer violations next push
5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated
