# Distributed Proposal: Kill the Import Phantom
*Generated 2026-04-10 16:02 UTC — 10 files contributed*

## Bug Summary
Type: `hardcoded_import` | Hosts: 7 | Flow traces: 3

## Diagnoses (0 from 10 files)

## Missing Context (0 requests)
*Files requesting information they need but cannot access:*

## Proposed Fixes (0)

## Operator Requests (0)

## Flow Trace Evidence
- **[failure]** file_heat_map (heat=0.35)
- **[targeted]** file_heat_map → logger → models → mutation_scorer → operator_stats → pulse_harvest → push_narrative → query_memory → resistance_bridge → rework_backfill (heat=0.54)
- **[heat]** file_heat_map → logger → models → mutation_scorer → operator_stats → pulse_harvest → push_narrative → query_memory (heat=0.54)

## Node Memory (what files have learned)
- **mutation_scorer**: score=0.489, samples=22
- **push_narrative**: score=0.558, samples=29
- **cli**: score=0.000, samples=0
- **vein_transport**: score=0.000, samples=0
- **dev_plan**: score=0.000, samples=0
- **resistance_bridge**: score=0.395, samples=11
- **operator_stats**: score=0.559, samples=22
- **models**: score=0.072, samples=167
- **query_memory**: score=0.512, samples=19
- **gemini_chat**: score=0.000, samples=0

---
*Import Phantom says: "I inhabit 7 modules. Kill me if you can."*