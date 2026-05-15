# Bug Profiles — The Rogues Gallery

*Auto-generated 2026-05-10 15:38 UTC · 15 modules carrying bugs · 3 species identified*

> Every bug here is alive. They have names, habits, and a body count.
> This page tells you who they are, what they're doing to your codebase, and what to do about it.

## The Lineup

**Dead Export Shade** (`de`) — 1 module, 2 total sightings. *Leaves dead functions standing so everyone thinks they matter.*

**Coupling Leech** (`hc`) — 9 modules, 9 total sightings. *Braids modules together until one cut hurts five files.*

**Overcap Maw** (`oc`) — 6 modules, 7 total sightings. *Swells files past the hard cap. Split before it eats context.*

## Filename β Check

The β suffix in a filename is the bug's brand. If it's missing, pigeon lost track.

- `codex_compat_append_jsonl` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_ensure_repo_on_path` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_load_json` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_load_jsonl_tail` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_parse_deleted_words` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_refresh_state` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_render_dynamic_context_pack` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_repo_root` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_select_context` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `codex_compat_utc_now` — should be βhc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `batch_rewrite_sim` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `intent_outcome_binder` — should be βdeoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `operator_response_policy` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.

2/15 branded correctly. 13 missing — next rename cycle should catch them.

---
## Dead Export Shade

*Leaves dead functions standing so everyone thinks they matter.* — 1 known host.

### intent_outcome_binder

*Demon name: Export Shade of intentou*

`intent_outcome_binder` has 1 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 2x across 2 versions. β in filename: **MISSING**.


---
## Coupling Leech

*Braids modules together until one cut hurts five files.* — 9 known hosts.

### codex_compat_append_jsonl

*Demon name: Tangle Fiend of codexcom*

`codex_compat_append_jsonl` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_ensure_repo_on_path

*Demon name: Coupling Leech of codexcom*

`codex_compat_ensure_repo_on_path` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_load_json

*Demon name: Tangle Fiend of codexcom*

`codex_compat_load_json` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_load_jsonl_tail

*Demon name: Knot Familiar of codexcom*

`codex_compat_load_jsonl_tail` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_parse_deleted_words

*Demon name: Tangle Fiend of codexcom*

`codex_compat_parse_deleted_words` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_refresh_state

*Demon name: Tangle Fiend of codexcom*

`codex_compat_refresh_state` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_repo_root

*Demon name: Knot Familiar of codexcom*

`codex_compat_repo_root` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_select_context

*Demon name: Tangle Fiend of codexcom*

`codex_compat_select_context` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### codex_compat_utc_now

*Demon name: Tangle Fiend of codexcom*

`codex_compat_utc_now` braided itself to (unknown) so tightly that touching one means touching all 0. Extract the shared logic into a common module. Or accept the pain every time you edit.

Spotted 1x across 2 versions. β in filename: **MISSING**.


---
## Overcap Maw

*Swells files past the hard cap. Split before it eats context.* — 6 known hosts.

### intent_outcome_binder

*Demon name: Overcap Maw of intentou*

`intent_outcome_binder` came in wheezing at 5433 tokens — that's 172% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 2 versions. β in filename: **MISSING**.

### codex_compat_render_dynamic_context_pack

*Demon name: Split Fiend of codexcom*

`codex_compat_render_dynamic_context_pack` came in wheezing at 2316 tokens — that's 16% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### w_gpmo

*Demon name: Split Fiend of wgpmo*

`w_gpmo` came in wheezing at 8280 tokens — that's 314% over the 2000-token hard cap. Every push it gains weight. v12, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 12 versions. β in filename: yes.

### 净拆f_rcs

*Demon name: Overcap Maw of frcs*

`净拆f_rcs` came in wheezing at 2343 tokens — that's 17% over the 2000-token hard cap. Every push it gains weight. v7, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 7 versions. β in filename: yes.

### batch_rewrite_sim

*Demon name: Shard Hunger of batchrew*

`batch_rewrite_sim` came in wheezing at 16929 tokens — that's 746% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 2 versions. β in filename: **MISSING**.

### operator_response_policy

*Demon name: Shard Hunger of operator*

`operator_response_policy` came in wheezing at 3186 tokens — that's 59% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 2 versions. β in filename: **MISSING**.

