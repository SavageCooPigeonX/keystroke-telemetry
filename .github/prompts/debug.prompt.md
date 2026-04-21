---
description: "Debug-focused context: known issues, fragile contracts, clots, dossier"
---

# /debug (RECOMMENDED)

*Hydrated 2026-04-21 23:15 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.495
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`neutral` bl_wpm=53 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Known Issues (from self-fix scanner)

- [CRITICAL] hardcoded_import in `scripts/bug_probe_hardcoded_import.py`
- [CRITICAL] hardcoded_import in `scripts/verify_loop_2.py`

## Fragile Contracts

- contracts. If a renamed module’s function signature changed silently, my imports will break at runtime.
- contract breaks, my API calls may send invalid parameters.
- contract, import statements in all renamed dependents, test suite import failures. This push standardizes the core word-number mapping filename across
- assumption breaks—for instance, if downstream consumers expect the old module name in dynamic imports—the entire import chain will fail silently. Watc
- contract with the pigeon registry’s naming schema; if that schema changes or the compiler’s extraction heuristic misinterprets the rename as a split, 
- assumption is that the orchestrator fires on every state change; if the daemon's event emission is throttled or batched, I may miss transitions. Watch

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

**Focus modules:** micro_sim_engine_prompt_file, word_number_file_mapping_for, gemini_api_call_system_prompt, picks_relevant_source_files_based, intent_simulation_on_typing_pause
**Focus bugs:** oc, de
