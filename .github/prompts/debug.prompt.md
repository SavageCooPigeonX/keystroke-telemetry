---
description: "Debug-focused context: known issues, fragile contracts, clots, dossier"
---

# /debug (RECOMMENDED)

*Hydrated 2026-04-23 16:28 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`debugging` state=`unknown` bl_wpm=52 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Known Issues (from self-fix scanner)

- [CRITICAL] hardcoded_import in `scripts/verify_loop_2.py`
- [CRITICAL] hardcoded_import in `tests/interlink/test_tc_web.py`

## Fragile Contracts

- assumption could break if prompt forms are not yet fully initialized or if the simulation engine lacks the necessary state isolation, leading to race
- breaks.
- breaks. If the operator works slowly, I may fire false simulations. I send intent predictions to **tc_sim_engine**; if my output schema drifts, the si
- break immediately. I test **git_plugin** and **intent_outcome_binder**; if their APIs change, I’ll throw runtime errors.
- break.
- break. Watch for my test being silently skipped due to a malformed or empty test case.

## Codebase Clots (dead/bloated)

- `classify_bridge`: orphan_no_importers, unused_exports:1, oversize:877
- `逆f_ba_bp_s005_v003_d0328_λR`: orphan_no_importers, unused_exports:1
- `学f_ll_cu_s006_v003_d0327_λγ`: orphan_no_importers, unused_exports:1
- `算f_ps_ca_s009_v002_d0327_λS`: orphan_no_importers, unused_exports:1
- `预p_pr_co_s001_v001`: orphan_no_importers, unused_exports:1

## Overcap Files (split candidates)

- `tc_sim` (14095 tok)
- `tc_gemini` (11314 tok)
- `tc_observatory` (11262 tok)
- `u_pj` (10995 tok)
- `tc_popup` (6993 tok)
- `w_gpmo` (6982 tok)
- `w_gpmo` (6980 tok)
- `tc_popup` (6892 tok)

## Active Bug Dossier

**Focus modules:** pulse_harvest_pairs_prompts_to, pigeon_extracted_by_compiler, primary_pigeon_observatory_window, passive_always_on_top_tkinter, replay_typed_sessions_through_the
**Focus bugs:** oc
