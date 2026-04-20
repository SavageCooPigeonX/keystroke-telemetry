# What The System Knows Right Now

*Auto-generated 2026-04-20 12:55 UTC · 812 prompts · 25 rework entries · zero LLM calls*

> This report is rewritten on every push. Every prediction becomes pass/fail when the next push lands.
> All signals are measured from live telemetry — nothing is inferred or hallucinated.

## What Gets Touched Next

*200 scored predictions · zero LLM calls*


> **Prediction bias:** chronically over-predicts `file_heat_map`, `import_rewriter`, `file_writer` — operator thinks about them more than they touch them

### Blind Spots *[source: measured]*
*Edited without being predicted — the real surprises:*
- `__main__` — 200x unpredicted
- `__init__` — 150x unpredicted
- `audit_loops` — 50x unpredicted
- `git_plugin_main_orchestrator` — 50x unpredicted
- `master_test` — 50x unpredicted

## Live Operator State

*812 prompts profiled · source: measured*

**Dominant: `abandoned` | Submit: 66% | Del: 6.9%**
- operator entering restructuring mode — expect more deletions than new code

## Pair Performance

*26 responses scored · 0 background excluded*

**Accuracy: 100% OK | 0% miss** *[source: measured]*
- trend: **stable** (100% → 100%)

**Prompt→edit latency:** 576.7s median (71 pairs)

### Mutation Effectiveness *[source: measured]*
*148 mutations scored*
- no significant signal yet — all sections scored neutral

**Reactor:** 531 fires, 2 accepted (0%)
> **Directive:** Reactor patches near-zero acceptance — tune confidence threshold or disable

## Codebase Health

*67 self-fix reports · 2026-03-16 → 2026-04-20*

**Problem trend: improving** (early avg 24 → recent avg 17) *[source: measured]*
- self-fix pipeline is containing technical debt

### Fragile Contracts *[source: llm_derived]*
*From push narratives — treat as hypothesis:*
- REGRESSION WATCHLIST: Downstream dynamic imports broken by the rename; pigeon compiler misinterpreting rename as a file split; dangling compiler artifact causing build collisions.

## Unsaid Threads

*Deleted from prompts — operator wanted this but did not ask:*

- "aff"
- "ffofoo"
- "ssw"
- "000"
- "fofoforr  sstttaaallleeenneneesssssshhhmmmmmm   hhhooowww   shshshooouuuldldld   iii"
- "w wririritetete   aaa"
- "rrr"
- "iss"
- "elc"
- "ggg"

## Confidence

*How much to trust this report:*

- **Rework signal:** WEAK (placeholder data) — 29 entries, 1 unique scores in last 20
- **Training pairs:** 193 captured
- **Prediction accuracy:** F1=0.000, calibration=0.155 (200 scored)
  - predictions near-random — treat all forecasts as hypotheses
- **Memory shards:** 11 active (zero LLM calls)

### Hypotheses Under Test
*These predictions become pass/fail on next push:*

1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited
2. **Deletion trend predicts mode** — rising deletion → restructuring, not building
3. **Rework trajectory holds** — if improving, fewer misses next push
4. **Self-fix converging** — if problem count falling, fewer violations next push
5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated
