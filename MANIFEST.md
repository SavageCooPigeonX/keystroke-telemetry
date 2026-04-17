# ORGANISM HEALTH — keystroke-telemetry

*Auto-generated 2026-04-15 01:04 UTC · 1423 Python files tracked · 0 prompts analyzed*

**This document is the organism. Every data pipeline that flows through this codebase is measured here. If it's not flowing, it's dying.**

---

## Vitals

| Metric | Value | Baseline |
|---|---|---|
| Cognitive State | **unknown** | — |
| Prompts Analyzed | 0 | — |
| Session Message | #? | — |
| Last Active | never (⚫) | — |
| Reactor Fires | 529 | — |

---

## Blood Flow (Data Pipelines)

| Pipeline | Entries | Size | Freshness | Role |
|---|---:|---:|---|---|
| prompt_journal | ? | 835,072 | 🟡 1h ago | Enriched prompts |
| chat_compositions | 4319 | 6.3M | 🟡 1h ago | Keystroke compositions |
| edit_pairs | 112 | 48,993 | 🔴 2d ago | Prompt → file pairings |
| push_cycles | 19 | 71,646 | 🔴 1d ago | Push cycle reports |
| os_keystrokes | 177791 | 41.5M | 🟡 1h ago | OS-level keystrokes |
| keystroke_live | 15594 | 4.6M | 🟢 1m ago | Live keystroke stream |
| rework_log | 200 | 39,300 | 🟡 1h ago | AI answer quality |
| file_heat_map | 55 | 8,991 | 🟡 1h ago | Cognitive load per module |
| file_profiles | 254 | 223,585 | 🔴 10d ago | Module consciousness |
| pigeon_registry | 2531 | 1.1M | 🟡 20h ago | Module registry |
| execution_deaths | 0 | 2 | 🟡 1h ago | Electron failures |
| context_veins | 7 | 424,073 | 🟡 22h ago | Vein/clot health |
| mutation_scores | 6 | 7,780 | 🔴 3d ago | Prompt mutation correlation |
| task_queue | 42 | 41,675 | 🟡 1h ago | Copilot task queue |
| push_cycle_state | 6 | 232 | 🔴 1d ago | Push cycle state |
| reactor_state | 4 | 19,595 | 🟡 1h ago | Reactor state |

---

## Structure (Module Compliance)

**1423 Python files** across 8 packages · **1314/1423 compliant** (92%) · **109 over cap**

| Package | Files |
|---|---:|
| `src` | 797 |
| `pigeon_compiler` | 255 |
| `pigeon_brain` | 213 |
| `tests` | 114 |
| `streaming_layer` | 21 |
| `(root)` | 14 |
| `client` | 7 |
| `vscode-extension` | 2 |

### Over-Cap Files (>200 lines)

| File | Lines | Severity |
|---|---:|---|
| `src/profile_chat_server.py` | 1280 | 🔴 CRIT |
| `autonomous_dev_stress_test.py` | 999 | 🔴 CRIT |
| `src/profile_renderer.py` | 925 | 🔴 CRIT |
| `vscode-extension/classify_bridge.py` | 877 | 🔴 CRIT |
| `client/os_hook.py` | 736 | 🔴 CRIT |
| `_run_smart_rename.py` | 730 | 🔴 CRIT |
| `_build_organism_health.py` | 728 | 🔴 CRIT |
| `src/环w_pc_s025_v003_d0330_读唤任_λπ.py` | 663 | 🔴 CRIT |
| `src/entropy_shedding.py` | 650 | 🔴 CRIT |
| `src/push_baseline.py` | 641 | 🔴 CRIT |
| `pigeon_brain/flow/算f_ps_s014_v006_d0404_译改名踪_λNU_βoc.py` | 636 | 🔴 CRIT |
| `client/chat_composition_analyzer.py` | 628 | 🔴 CRIT |
| `src/intent_reconstructor.py` | 628 | 🔴 CRIT |
| `src/tc_context_agent.py` | 625 | 🔴 CRIT |
| `src/file_semantic_layer.py` | 615 | 🔴 CRIT |
| `src/template_selector.py` | 613 | 🔴 CRIT |
| `src/思f_cr_s014_v005_d0331_译改名踪_λM.py` | 613 | 🔴 CRIT |
| `src/研w_rl_s029_v005_d0401_译改名踪_λG.py` | 613 | 🔴 CRIT |
| `src/bug_demon_hunt.py` | 608 | 🔴 CRIT |
| `src/tc_intel_report.py` | 601 | 🔴 CRIT |
| ... | +89 more | |

---

## Circulation (Dependency Health)

**598/630 alive** · 32 clots · 50 arteries · avg vein health: 0.51 · 938 edges

### Critical Arteries (do NOT break)

| Module | In-Degree | Vein Score |
|---|---:|---:|
| `gemini_chat` | 6 | 1.0 |
| `w_pl_s002_v005_d0401_册追跑谱桥_λA` | 5 | 1.0 |
| `册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc` | 16 | 1.0 |
| `追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc` | 12 | 1.0 |
| `净拆f_rcs_s010_v006_d0322_译测编深划_λW` | 5 | 1.0 |
| `copilot_prompt_manager_seq020_v003_d0402__compatibility_wrapper_for_the_legacy_lc_restore_rename_safe` | 6 | 1.0 |
| `u_pe_s024_v004_d0403_λP0_βoc` | 11 | 1.0 |
| `修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc` | 13 | 1.0 |
| `叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc` | 8 | 1.0 |
| `对p_tp_s027_v003_d0402_缩分话_λVR_βoc` | 7 | 1.0 |

### Clots (dead/bloated)

| Module | Score | Signals |
|---|---:|---|
| `f_he_s009_v005_d0401_改名册追跑_λA` | 0.7 | orphan_no_importers, dead_imports:2, unused_exports:1, oversize:256 |
| `bug_profiles` | 0.65 | orphan_no_importers, dead_imports:1, unused_exports:1, oversize:309 |
| `批编f_rbc_ma_s001_v001` | 0.6 | orphan_no_importers, dead_imports:3, unused_exports:1 |
| `偏p_dr_s003_v002_d0315_缩分话_λν` | 0.6 | orphan_no_importers, unused_exports:1, oversize:227 |
| `classify_bridge` | 0.6 | orphan_no_importers, unused_exports:1, oversize:877 |
| `f_he_gf_s002_v001` | 0.55 | orphan_no_importers, dead_imports:2, unused_exports:1 |
| `谱建f_mb_bam_s031_v001` | 0.55 | orphan_no_importers, dead_imports:2, unused_exports:1 |
| `逆f_ba_bp_s005_v003_d0328_λR` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `存p_nm_co_s001_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `算f_ps_ca_s009_v002_d0327_λS` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `预p_pr_co_s001_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `牌f_nam_bu_s005_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `.operator_stats_seq008_v010_d0331__persi_artifact_detection_seq003_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `隐p_un_di_s002_v003_d0322_λ7` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `u_oscl_s003_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `u_pj_s019_v002_d0402_λC_build_snapshot_decomposed_seq012_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `修f_sf_aaif_s011_v002_d0329_λH` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_apply_import_fixes_seq012_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `忆p_qm_cl_s004_v002_d0329_λH` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |
| `控f_ost_ad_s003_v001` | 0.5 | orphan_no_importers, dead_imports:1, unused_exports:1 |

---

## Hot Modules (Cognitive Load)

**55 modules tracked**

| Module | Avg Hesitation | Avg WPM | Samples | Dominant State |
|---|---:|---:|---:|---|
| `虚f_mc` | 0.000 | 0 | 0 | ? |
| `query_memory` | 0.000 | 0 | 0 | ? |
| `confidence_scorer` | 0.000 | 0 | 0 | ? |
| `thought_completion` | 0.000 | 0 | 0 | ? |
| `numeric_surface` | 0.000 | 0 | 0 | ? |
| `rework_detector` | 0.000 | 0 | 0 | ? |
| `training_pairs` | 0.000 | 0 | 0 | ? |
| `context_router` | 0.000 | 0 | 0 | ? |
| `copilot_prompt_manager` | 0.000 | 0 | 0 | ? |
| `training_writer` | 0.000 | 0 | 0 | ? |
| `self_fix` | 0.000 | 0 | 0 | ? |
| `symbol_dictionary` | 0.000 | 0 | 0 | ? |
| `operator_probes` | 0.000 | 0 | 0 | ? |
| `shard_manager` | 0.000 | 0 | 0 | ? |
| `警p_sa` | 0.000 | 0 | 0 | ? |

---

## Rework Surface (AI Response Quality)

**200 responses scored** · avg rework score: 0.07

| Verdict | Count | % |
|---|---:|---:|
| ok | 179 | 90% |
| miss | 12 | 6% |
| partial | 9 | 4% |

### Reworked Responses (138)

| Time | Score | Del% | Query Hint |
|---|---:|---:|---|
| 3h ago | 0.35 | 9% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.35 | 9% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.35 | 9% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.04 | 8% | bg:idle |
| 3h ago | 0.04 | 8% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.04 | 8% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.04 | 8% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.04 | 8% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 3h ago | 0.04 | 8% | bg:tc_profile_intelligence_orchestrator_seq024_v001.py |
| 1h ago | 0.20 | 10% | bg:idle |

---

## Prompt Consolidation

*No journal entries.*

---

## Push Cycle

| Metric | Value |
|---|---|
| Total Cycles | 19 |
| Last Commit | `beda89cc9fb13dfd4f32cf84bb2b966225efe853` |
| Last Sync Score | 0.058 |
| Journal Line | 614 |
| Updated | 1d ago |

---

## Task Queue

| ID | Task | Status |
|---|---|---|
| tq-001 | STRESS TEST: Learning loop verification | pending |
| tq-002 | hey all asked me the same question ow should the context sel... | done |
| tq-003 | why is deepseek not set and how did git push fail hellp... (... | done |
| tq-004 | run tests - does question injection into copilotwork okay do... | done |
| tq-005 | hmm - run stress tests - sim some completions to get context... | done |
| tq-006 | exept in vibe coding the cognitive state usually changes per... | done |
| tq-007 | also the thought completer should be completing thought for ... | done |
| tq-008 | because the whole point of the thought completer is to step ... | done |
| tq-009 | no no no the thought completer is the feedback loop... (also... | done |
| tq-010 | youre not understanding - you have a way to ask questions - ... | done |
| tq-011 | compare that to current copilot prompt templates - aseess wh... | done |
| tq-012 | the rename engine should alread append why file names were t... | done |
| tq-013 | yeah but youre not mapping how the context select / tc build... | done |
| tq-014 | write a FRBI report (search online for federal reality burea... | done |
| tq-015 | yes but the refusals must have 18 queries that cannot be hel... | done |
| tq-016 | wait isint sleep mode / 10 questions from blade runner 2049 ... | done |
| tq-017 | hm  whats the actual fix for tc to finish thinking my though... | done |
| tq-018 | run push cycle - we should have 50? or so file simulations h... | done |
| tq-019 | perfect  - i think im ready to focus on what i call an IRT -... | done |
| tq-020 | aybe not quite yet - hmmm -  how do we have intent reinjecti... | done |
| tq-021 | can you make sure that website obervatory is launched with v... | done |
| tq-022 | probably do a push cycle - check if self fix / push narrativ... | done |
| tq-023 | okay so based off the intel report i think the thought compl... | done |
| tq-024 | else is left untill the insane self healing works | done |
| tq-025 | ththought completer has two headers where you can close it -... | done |
| tq-026 | take all 4 steps - fix thought completer being shit - it nee... | done |
| tq-027 | check entropy map accumulation / self execution - i just add... | done |
| tq-028 | quick question for you - why do llm matchers go by words not... | done |
| tq-029 | bur assuming future operators type less words / steer styste... | done |
| tq-030 | whats the actual proper way to do this system - we leeep mis... | done |
| tq-031 | no no no not even that - i just want to make it so that whil... | done |
| tq-032 | resynth my last 28 prompts / check codebase status against m... | pending |
| tq-033 | retrack my last 12 prompts to resynthesize intent / make imp... | pending |
| tq-034 | also seach online. coo coo zap | pending |
| tq-035 | write new report - novel info only | pending |
| tq-036 | mehh i still dont blive it works - you models always say it ... | pending |
| tq-037 | how can we use savagecoopigeonx research on christ is king /... | pending |
| tq-038 | if you strip all roleplay is there any logic in embedding ch... | pending |
| tq-039 | didnt we already build out questions?? | pending |
| tq-040 | make assesment happen on push to measure drift - and include... | pending |
| tq-041 | you were also gonna say isint working - its not simming my i... | pending |
| tq-042 | i want to inspect he semantic layer of each file - like ever... | pending |

---

## Death Log (Execution Failures)

*No execution deaths recorded.*

---


*Regenerate: `py _build_organism_health.py` · Wire into `git_plugin.py` post-commit for auto-refresh.*
