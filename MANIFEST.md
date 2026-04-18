# ORGANISM HEALTH — keystroke-telemetry

*Auto-generated 2026-04-18 05:11 UTC · 1472 Python files tracked · 0 prompts analyzed*

**This document is the organism. Every data pipeline that flows through this codebase is measured here. If it's not flowing, it's dying.**

---

## Vitals

| Metric | Value | Baseline |
|---|---|---|
| Cognitive State | **unknown** | — |
| Prompts Analyzed | 0 | — |
| Session Message | #? | — |
| Last Active | never (⚫) | — |
| Reactor Fires | 531 | — |

---

## Blood Flow (Data Pipelines)

| Pipeline | Entries | Size | Freshness | Role |
|---|---:|---:|---|---|
| prompt_journal | ? | 888,594 | 🟢 3m ago | Enriched prompts |
| chat_compositions | 4376 | 6.4M | 🟢 3m ago | Keystroke compositions |
| edit_pairs | 112 | 48,993 | 🟢 1m ago | Prompt → file pairings |
| push_cycles | 20 | 74,880 | 🟡 8h ago | Push cycle reports |
| os_keystrokes | 188666 | 44.2M | 🟢 3m ago | OS-level keystrokes |
| keystroke_live | 15937 | 4.7M | 🟢 2m ago | Live keystroke stream |
| rework_log | 197 | 40,168 | 🟢 2m ago | AI answer quality |
| file_heat_map | 57 | 9,307 | 🟢 2m ago | Cognitive load per module |
| file_profiles | 254 | 223,585 | 🔴 14d ago | Module consciousness |
| pigeon_registry | 2531 | 1.4M | 🟢 35m ago | Module registry |
| execution_deaths | 0 | 2 | 🟡 23h ago | Electron failures |
| context_veins | 7 | 425,270 | 🟢 4m ago | Vein/clot health |
| mutation_scores | 6 | 7,780 | 🔴 6d ago | Prompt mutation correlation |
| task_queue | 28 | 25,457 | 🟡 4h ago | Copilot task queue |
| push_cycle_state | 6 | 200 | 🟡 8h ago | Push cycle state |
| reactor_state | 4 | 21,747 | 🟢 2m ago | Reactor state |

---

## Structure (Module Compliance)

**1472 Python files** across 9 packages · **1359/1472 compliant** (92%) · **113 over cap**

| Package | Files |
|---|---:|
| `src` | 802 |
| `pigeon_compiler` | 256 |
| `pigeon_brain` | 213 |
| `tests` | 136 |
| `streaming_layer` | 21 |
| `scripts` | 18 |
| `(root)` | 17 |
| `client` | 7 |
| `vscode-extension` | 2 |

### Over-Cap Files (>200 lines)

| File | Lines | Severity |
|---|---:|---|
| `src/profile_chat_server.py` | 1280 | 🔴 CRIT |
| `autonomous_dev_stress_test.py` | 999 | 🔴 CRIT |
| `src/profile_renderer.py` | 925 | 🔴 CRIT |
| `vscode-extension/classify_bridge.py` | 877 | 🔴 CRIT |
| `src/vitals_renderer.py` | 783 | 🔴 CRIT |
| `client/os_hook.py` | 736 | 🔴 CRIT |
| `src/tc_gemini.py` | 731 | 🔴 CRIT |
| `_run_smart_rename.py` | 730 | 🔴 CRIT |
| `_build_organism_health.py` | 728 | 🔴 CRIT |
| `src/环w_pc_s025_v003_d0330_读唤任_λπ.py` | 663 | 🔴 CRIT |
| `src/entropy_shedding.py` | 650 | 🔴 CRIT |
| `src/push_baseline.py` | 641 | 🔴 CRIT |
| `pigeon_brain/flow/算f_ps_s014_v006_d0404_译改名踪_λNU_βoc.py` | 636 | 🔴 CRIT |
| `src/tc_context_agent.py` | 630 | 🔴 CRIT |
| `client/chat_composition_analyzer.py` | 628 | 🔴 CRIT |
| `src/intent_reconstructor.py` | 628 | 🔴 CRIT |
| `src/file_semantic_layer.py` | 615 | 🔴 CRIT |
| `src/template_selector.py` | 613 | 🔴 CRIT |
| `src/思f_cr_s014_v005_d0331_译改名踪_λM.py` | 613 | 🔴 CRIT |
| `src/研w_rl_s029_v005_d0401_译改名踪_λG.py` | 613 | 🔴 CRIT |
| ... | +93 more | |

---

## Circulation (Dependency Health)

**596/630 alive** · 34 clots · 50 arteries · avg vein health: 0.51 · 938 edges

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

**57 modules tracked**

| Module | Avg Hesitation | Avg WPM | Samples | Dominant State |
|---|---:|---:|---:|---|
| `entropy_shedding` | 0.000 | 0 | 0 | ? |
| `unsaid_recon` | 0.000 | 0 | 0 | ? |
| `file_semantic_layer` | 0.000 | 0 | 0 | ? |
| `symbol_dictionary` | 0.000 | 0 | 0 | ? |
| `unified_signal` | 0.000 | 0 | 0 | ? |
| `_build_prompt` | 0.000 | 0 | 0 | ? |
| `dynamic_prompt` | 0.000 | 0 | 0 | ? |
| `vitals_renderer` | 0.000 | 0 | 0 | ? |
| `training_writer` | 0.000 | 0 | 0 | ? |
| `confidence_scorer` | 0.000 | 0 | 0 | ? |
| `escalation_engine` | 0.000 | 0 | 0 | ? |
| `voice_style` | 0.000 | 0 | 0 | ? |
| `query_memory` | 0.000 | 0 | 0 | ? |
| `mutation_scorer` | 0.000 | 0 | 0 | ? |
| `虚f_mc` | 0.000 | 0 | 0 | ? |

---

## Rework Surface (AI Response Quality)

**197 responses scored** · avg rework score: 0.10

| Verdict | Count | % |
|---|---:|---:|
| ok | 173 | 88% |
| partial | 20 | 10% |
| miss | 4 | 2% |

### Reworked Responses (24)

| Time | Score | Del% | Query Hint |
|---|---:|---:|---|
| 3h ago | 0.33 | 5% | bg:__init__.py |
| 3h ago | 0.33 | 5% | bg:__init__.py |
| 3h ago | 0.62 | 31% | bg:__init__.py |
| 1h ago | 0.29 | 25% | bg:tc_context.py |
| 1h ago | 0.29 | 25% | bg:prediction_scores.json |
| 1h ago | 0.29 | 25% | bg:prediction_scores.json |
| 23m ago | 0.20 | 10% | bg:BUG_PROFILES.md |
| 7m ago | 0.38 | 68% | bg:BUG_PROFILES.md |
| 6m ago | 0.38 | 68% | bg:BUG_PROFILES.md |
| 6m ago | 0.38 | 68% | bg:BUG_PROFILES.md |

---

## Prompt Consolidation

*No journal entries.*

---

## Push Cycle

| Metric | Value |
|---|---|
| Total Cycles | 20 |
| Last Commit | `46867e94` |
| Last Sync Score | 0.016 |
| Journal Line | 687 |
| Updated | 8h ago |

---

## Task Queue

| ID | Task | Status |
|---|---|---|
| tq-001 | hm  whats the actual fix for tc to finish thinking my though... | done |
| tq-002 | run push cycle - we should have 50? or so file simulations h... | done |
| tq-003 | why is entropy still staying in the 0.80s while you edit | done |
| tq-004 | >>> diagnose and fix every datapoint that is being hallucnat... | done |
| tq-005 | in copilot instruction. hallucination audit | done |
| tq-006 | perfect  - i think im ready to focus on what i call an IRT -... | done |
| tq-007 | aybe not quite yet - hmmm -  how do we have intent reinjecti... | done |
| tq-008 | can you make sure that website obervatory is launched with v... | done |
| tq-009 | the visualizartion needs to be reworked to be the most optim... | pending |
| tq-010 | why is organism health still so low - audit copilot intructi... | pending |
| tq-011 | not talk first - when i click on a file throught pgeon brain... | pending |
| tq-012 | youre shedding the wrong blocks too - instead of entropy you... | pending |
| tq-013 | no no our visualitions are spreadacrpss 3 uis - i need one w... | pending |
| tq-014 | <conversation-summary>
<analysis>
[Chronological Review:
- T... | pending |
| tq-015 | >> i want  to click on profiles / have seperate page per pro... | pending |
| tq-016 | we keep on having disk issues  due to lack of refresh - good... | pending |
| tq-017 | You were about to complete but a hook blocked you with the f... | pending |
| tq-018 | what would wakr my codebase up - what autonomous action has ... | pending |
| tq-019 | diagnose why autonomous fixes are there - why i have a shit ... | pending |
| tq-020 | shit content / chats dont work ui is currently useless needs... | pending |
| tq-021 | you still dont have it quite right - when i click on a file ... | pending |
| tq-022 | check prompt history / intent backlog - run push cycle and o... | pending |
| tq-023 | when i click on a file - it need to wake up and do a self an... | pending |
| tq-024 | gemini is dead apperantly - use deepseek | pending |
| tq-025 | if you work just based off my recontructed event and got con... | pending |
| tq-026 | nope i want you to go ahead and do the loop | pending |
| tq-027 | why do you keep stopping work | pending |
| tq-028 | can you fix whatever bug youre having thats stopping you fro... | pending |

---

## Death Log (Execution Failures)

*No execution deaths recorded.*

---


*Regenerate: `py _build_organism_health.py` · Wire into `git_plugin.py` post-commit for auto-refresh.*
