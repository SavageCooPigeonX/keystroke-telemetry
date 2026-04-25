# Architecture Pivot: Thought Completer as Primary Organ

**Date:** 2026-04-23
**Supersedes:** parts of `ARCHITECTURE_CONSENSUS_v3.md` related to product centering

---

## What changed

Prior architecture (v3 consensus) centered on 18 capture/compliance queries
with no single primary organ. Coding loop, organism metaphor, and telemetry
all sat at the same tier with no explicit ordering.

**New centering:** the **thought completer** is the primary organ. Every
other daemon is either an input (capture), a shard (storage), or an
executor (copilot / deepseek / sim).

## The singular KPI

`intent_closure_rate = closed_intents_7d / total_intents_7d`

Replaces: organism health, compliance %, bug count, rework rate as top-line.

## Operator profile → multi-shard

The monolithic `operator_profile.md` and scattered state is replaced by
**self-managing shards** (vocabulary, cognition, learned_pairs,
file_affinity, correction_log, exploration, session_summary) governed by
**self-managing intent keys** (birth/growth/split/merge/sleep/death
lifecycle).

See `docs/THOUGHT_COMPLETER_PLAN.md` §3 for schema.

## Absorption list

These components collapse into the completer or become shard writers:

- `prompt_enricher` → completer rendering step
- `context_select_agent` → file-numeric module in completer
- `intent_backlog` → open-fragment queue
- `deleted_words` reconstruction → in-band exploration signal
- `operator_state_daemon` → cognition shard writer
- `prompt_telemetry` → vocabulary + cognition shard writer
- `operator_probes` → clarifying-question mode
- `intent_numeric` → intent key extraction core
- copilot-instructions `current-query` → completer live display

## Unchanged (peripherals)

- deepseek daemon, file_sim, self_fix scanner, pigeon compiler, entropy map,
  observatory, VS Code extension capture layer

## Open decisions tracked

See `docs/THOUGHT_COMPLETER_PLAN.md` §15.

## Next doc update

When Phase 0 (shard foundation) completes OR any open decision in §15
resolves.
