---
description: "Build-focused context: module map, file consciousness, coupling, commits"
---

# /build

*Hydrated 2026-04-10 16:20 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.494
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Deleted words:** should bug, > eg, - then, self, problems, leaks _, los san
**Unsaid threads:** should bug, - then, problems, leaks _, los san
**Rewrites:** "should bug" → "i w"; "ld f" → "lt by bug demon - it writes own own status - and bug report manifest chains acro"; "> eg" → "lmk what is tha"; "- then" → "in its own system / self imprr"
**Hot modules:** `file_heat_map` (hes=0.89), `import_rewriter` (hes=0.73), `file_writer` (hes=0.73)
**Codes:** intent=`exploring` state=`unknown` bl_wpm=54 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Module Map (compact)

**client** (7 modules, 9.4K tok)
**pigeon_brain** (24 modules, 15.2K tok)
**pigeon_brain/flow** (24 modules, 17.6K tok)
**pigeon_brain/flow/backward_seq007** (7 modules, 1.5K tok)
**pigeon_brain/flow/learning_loop_seq013** (14 modules, 2.3K tok)
**pigeon_brain/flow/node_memory_seq008** (9 modules, 795 tok)
**pigeon_brain/flow/prediction_scorer_seq014** (16 modules, 2.4K tok)
**pigeon_brain/flow/predictor_seq009** (10 modules, 1.7K tok)
**pigeon_compiler** (5 modules, 8.9K tok)
**pigeon_compiler/cut_executor** (12 modules, 3.2K tok)
**pigeon_compiler/integrations** (1 modules, 362 tok)
**pigeon_compiler/rename_engine** (12 modules, 11.8K tok)
**pigeon_compiler/rename_engine/compliance_seq008** (11 modules, 1.1K tok)
**pigeon_compiler/rename_engine/heal_seq009** (5 modules, 698 tok)
**pigeon_compiler/rename_engine/manifest_builder_seq007** (31 modules, 3.9K tok)
**pigeon_compiler/rename_engine/nametag_seq011** (8 modules, 741 tok)
**pigeon_compiler/rename_engine/registry_seq012** (9 modules, 996 tok)
**pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR** (13 modules, 1.4K tok)
**pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc** (12 modules, 1.4K tok)
**pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc** (11 modules, 1.7K tok)
**pigeon_compiler/runners** (9 modules, 4.6K tok)
**pigeon_compiler/runners/run_batch_compile_seq015** (3 modules, 653 tok)
**pigeon_compiler/state_extractor** (6 modules, 1.7K tok)
**pigeon_compiler/weakness_planner** (1 modules, 1.3K tok)
**src** (103 modules, 134.5K tok)
**src/.operator_stats_seq008_v010_d0331__persi** (9 modules, 2.1K tok)
**src/cognitive** (3 modules, 2.1K tok)
**src/cognitive/drift** (6 modules, 752 tok)
**src/cognitive/drift_seq003** (4 modules, 740 tok)
**src/cognitive/unsaid** (8 modules, 697 tok)
**src/cognitive/unsaid_seq002** (3 modules, 731 tok)
**src/operator_stats** (13 modules, 2.0K tok)
**src/u_pe_s024_v002_d0402_λC** (13 modules, 2.7K tok)
**src/u_pe_s024_v004_d0403_λP0_βoc** (10 modules, 2.2K tok)
**src/u_pj_s019_v002_d0402_λC** (17 modules, 3.1K tok)
**src/修_sf_s013** (11 modules, 2.2K tok)
**src/修f_sf_s013_v012_d0402_初写谱净拆_λVR** (16 modules, 2.3K tok)
**src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc** (12 modules, 2.2K tok)
**src/叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc** (7 modules, 918 tok)
**src/对p_tp_s027_v003_d0402_缩分话_λVR_βoc** (6 modules, 1.3K tok)
**src/忆_qm_s010** (6 modules, 552 tok)
**src/思_cr_s014** (14 modules, 2.6K tok)
**src/控_ost_s008** (9 modules, 2.1K tok)
**src/推_dp_s017** (15 modules, 2.3K tok)
**src/环_pc_s025** (9 modules, 2.0K tok)
**src/管_cpm_s020** (10 modules, 1.6K tok)
**src/管_cpm_s020/copilot_prompt_manager_seq020** (5 modules, 769 tok)
**src/管w_cpm_s020_v003_d0402_缩分话_λVR_βoc** (15 modules, 3.1K tok)
**src/脉_ph_s015** (7 modules, 826 tok)
**src/觉_fc_s019** (12 modules, 1.9K tok)
**src/警p_sa_s030_v003_d0402_缩分话_λV** (8 modules, 615 tok)
**streaming_layer** (20 modules, 3.5K tok)
**vscode-extension** (2 modules, 3.3K tok)

## Codebase Fears (from file consciousness)

- file may not exist (17 modules)
- returns empty on failure (silent) (14 modules)
- regex format dependency (11 modules)
- swallowed exception (10 modules)

## Recent Commits

- 4aedb96 feat: pitch sim + thought completer split + organism health fix + heat map rewrite + session awareness + anti-echo prompt + copilot context persistence
- af0652b feat: operator probes + prediction-driven probes + persona memory + entropy chart + file chat + thinned personality prompts + source code lookup fix
- 843fa29 fix: rebuild 36 broken __init__.py + fix 37 hardcoded pigeon_brain imports + add import_rewriter error logging
- 3e125f5 feat: entropy shedding + intent compressor + human-AI coding paradigm in system prompt + context compressor + codebase transmuter + self-fix tracker
- c461c19 chore(pigeon): auto-rename 8 file(s) [pigeon-auto]
- 5e29260 feat: numeric surface layer + narrative bug profiles + stale import fixes
- 38ea651 chore(pigeon): auto-rename 1 file(s) [pigeon-auto]
- 08b2b56 fix: add REGISTRY_FILE import to registry_io shard
