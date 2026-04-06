---
description: "Debug-focused context: known issues, fragile contracts, clots, dossier"
---

# /debug (RECOMMENDED)

*Hydrated 2026-04-06 01:33 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.495
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Deleted words:** readi, and what should we a, - it should work on push - like every push is a forced compression, apple, write me a recipie wor an apple pie, as python, autono, ;pat, - how much more soul
**Unsaid threads:** readi, and what should we a, - it should work on push - like every push is a forced compression, apple, write me a recipie wor an apple pie, as python, autono, - how much more soul
**Rewrites:** "apple" → "write me a recipie wor am"; "write me a recipie wor an apple pie" → "- checkif gemini reohraser triggers in cot - seq - version helpsllm in my oppini"; "math" → "think of that match this pattern of missrepresented thinking in code"; "as python" → "as words for pythong or something insane like that - pushi"
**Hot modules:** `file_heat_map` (hes=0.89), `import_rewriter` (hes=0.73), `file_writer` (hes=0.73)
**Active bugs:** `u_pe` (oc), `u_pj` (oc), `警p_sa` (oc), `册f_reg` (oc)
**Codes:** intent=`debugging` state=`neutral` bl_wpm=54 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Known Issues (from self-fix scanner)

- [CRITICAL] hardcoded_import in `pigeon_brain/令f_cl_s009_v002_d0323_缩分话_λP.py`

## Fragile Contracts

- breaking the entire injection chain. I provide validated rename maps to 追跑f_ruhe; if my output contract changes from a flat dict to a list, its healin
- breaking the prompt pipeline.
- breaking audit trails. Watch for prompts that lose their actor tags in downstream logs.
- contract changes and tags are not passed, the audit will flag valid prompts as invalid, causing narrative generation to halt. Watch for false‑positive
- breaking downstream attribution.
- break mid-cycle. I receive all cross-referenced data from u_pj and manage the injection lifecycle. If the surface object size balloons, my memory trac

## Codebase Clots (dead/bloated)

- `aim_utils`: orphan_no_importers, unused_exports:1
- `press_release_gen_constants_seq001_v001`: orphan_no_importers, unused_exports:1
- `adapter`: orphan_no_importers, unused_exports:1
- `query_memory`: dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory

## Overcap Files (split candidates)

- `streaming_layer` (10189 tok)
- `管w_cpm` (8012 tok)
- `u_pj` (7903 tok)
- `推w_dp` (5987 tok)
- `self_fix` (5846 tok)
- `修f_sf` (5829 tok)
- `prediction_scorer` (5797 tok)
- `算f_ps` (5782 tok)

## Active Bug Dossier

**Focus modules:** every_entry_cross_references_all, training_pair_generator_for_the, tracks_cognitive_load_per_module, copilot_self_diagnostic_detect_stale, local_name_registry_for_the
**Focus bugs:** de, oc
