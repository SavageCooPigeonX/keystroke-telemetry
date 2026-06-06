---
description: "Debug-focused context: known issues, fragile contracts, clots, dossier"
---

# /debug (RECOMMENDED)

*Hydrated 2026-06-06 00:02 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 44 | Del: 26% | Hes: 0.475
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `file_email_plugin` (oc+hc+de), `w_gpmo` (oc+hc), `codex_edit_outcome_binder` (oc+hc), `file_intent_identity` (oc+hc)
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Fragile Contracts

- assumption could break if prompt forms are not yet fully initialized or if the simulation engine lacks the necessary state isolation, leading to race 
- breaks.
- breaks. If the operator works slowly, I may fire false simulations. I send intent predictions to **tc_sim_engine**; if my output schema drifts, the si
- break immediately. I test **git_plugin** and **intent_outcome_binder**; if their APIs change, I’ll throw runtime errors.
- break.
- break. Watch for my test being silently skipped due to a malformed or empty test case.

## Codebase Clots (dead/bloated)

- `p_tcsr`: isolated, dead_imports:3, unused_exports:1
- `context_select_agent`: orphan_no_importers, dead_imports:1, unused_exports:1, oversize:275
- `p_tcm`: isolated, unused_exports:1
- `p_gpip`: orphan_no_importers, unused_exports:1
- `file_sim`: dead_imports:3, oversize:1344, self_fix:dead_export:apply_undo_penalty, self_fix:dead_export:escalation_sweep

## Overcap Files (split candidates)

- `registry_identity_bridge` (3485 tok)
- `intent_identity_naming` (2161 tok)
