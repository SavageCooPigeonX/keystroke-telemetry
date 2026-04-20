# What The System Knows Right Now

*Auto-generated 2026-04-20 00:18 UTC · 796 prompts · 200 rework entries · zero LLM calls*

> This report is rewritten on every push. Every prediction becomes pass/fail when the next push lands.
> All signals are measured from live telemetry — nothing is inferred or hallucinated.

## What Gets Touched Next

*200 scored predictions · zero LLM calls*


> **Prediction bias:** chronically over-predicts `file_heat_map`, `import_rewriter`, `file_writer` — operator thinks about them more than they touch them

### Blind Spots *[source: measured]*
*Edited without being predicted — the real surprises:*
- `__main__` — 100x unpredicted
- `_tmp_regen_dict` — 50x unpredicted
- `_tmp_token_audit` — 50x unpredicted
- `_tmp_token_optimizer` — 50x unpredicted
- `copilot_prompt_manager_seq020_auto_index_builder` — 50x unpredicted

## Live Operator State

*796 prompts profiled · source: measured*

**Dominant: `abandoned` | Submit: 66% | Del: 4.1%**
- operator entering restructuring mode — expect more deletions than new code

## Pair Performance

*200 responses scored · 0 background excluded*

**Accuracy: 100% OK | 0% miss** *[source: measured]*
- trend: **stable** (100% → 99%)

**Prompt→edit latency:** 576.7s median (71 pairs)

### Mutation Effectiveness *[source: measured]*
*143 mutations scored*
- no significant signal yet — all sections scored neutral

**Reactor:** 531 fires, 2 accepted (0%)
> **Directive:** Reactor patches near-zero acceptance — tune confidence threshold or disable

## Codebase Health

*63 self-fix reports · 2026-03-16 → 2026-04-20*

**Problem trend: growing** (early avg 24 → recent avg 30) *[source: measured]*
- problems growing ~6/push — expect more over_hard_cap and dead_exports without intervention

### Fragile Contracts *[source: llm_derived]*
*From push narratives — treat as hypothesis:*
- REGRESSION WATCHLIST: Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.

### Electron Killers *[source: measured]*
- `graph_heat_map` — 2 deaths/4 calls (50%)

## Unsaid Threads

*Deleted from prompts — operator wanted this but did not ask:*

- ",,   BBB...   CCCOOOppp"
- "yuu"
- "uuu"
- "d d d"
- "bbby y y"
- "iiit t t"
- "sww"
- "fww"
- "ppprrr"
- "sue"

## Confidence

*How much to trust this report:*

- **Rework signal:** GOOD — 200 entries, 3 unique scores in last 20
- **Training pairs:** 193 captured
- **Prediction accuracy:** F1=0.000, calibration=0.191 (200 scored)
  - predictions near-random — treat all forecasts as hypotheses
- **Memory shards:** 11 active (zero LLM calls)

### Hypotheses Under Test
*These predictions become pass/fail on next push:*

1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited
2. **Deletion trend predicts mode** — rising deletion → restructuring, not building
3. **Rework trajectory holds** — if improving, fewer misses next push
4. **Self-fix converging** — if problem count falling, fewer violations next push
5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated
