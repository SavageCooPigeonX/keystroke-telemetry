# ORGANISM HEALTH — keystroke-telemetry

*Auto-generated 2026-04-18 18:19 UTC · 1487 Python files tracked · 752 prompts analyzed*

**This document is the organism. Every data pipeline that flows through this codebase is measured here. If it's not flowing, it's dying.**

---

## Vitals

| Metric | Value | Baseline |
|---|---|---|
| Cognitive State | **unknown** | — |
| WPM (latest) | 0.0 | ? |
| Deletion Ratio | 0.0% | ? |
| Prompts Analyzed | 752 | — |
| Session Message | #3 | — |
| Last Active | 16m ago (🟢) | — |
| Reactor Fires | 531 | — |

---

## Blood Flow (Data Pipelines)

| Pipeline | Entries | Size | Freshness | Role |
|---|---:|---:|---|---|
| prompt_journal | 752 | 967,892 | 🟢 16m ago | Enriched prompts |
| chat_compositions | 4397 | 6.4M | 🟢 16m ago | Keystroke compositions |
| edit_pairs | 121 | 72,674 | 🟢 19m ago | Prompt → file pairings |
| push_cycles | 20 | 74,880 | 🟡 21h ago | Push cycle reports |
| os_keystrokes | 191307 | 44.8M | 🟢 16m ago | OS-level keystrokes |
| keystroke_live | 16067 | 4.7M | 🟢 48s ago | Live keystroke stream |
| rework_log | 200 | 40,970 | 🟢 3m ago | AI answer quality |
| file_heat_map | 66 | 10,790 | 🟢 3m ago | Cognitive load per module |
| file_profiles | 254 | 223,585 | 🔴 14d ago | Module consciousness |
| pigeon_registry | 2531 | 1.5M | 🟢 3m ago | Module registry |
| execution_deaths | 0 | 2 | 🔴 1d ago | Electron failures |
| context_veins_seq001_v001 | 7 | 411,904 | 🟢 41s ago | Vein/clot health |
| mutation_scores | 6 | 7,780 | 🔴 7d ago | Prompt mutation correlation |
| task_queue | 28 | 25,457 | 🟢 35m ago | Copilot task queue |
| push_cycle_state | 6 | 200 | 🟡 21h ago | Push cycle state |
| reactor_state | 4 | 22,069 | 🟢 3m ago | Reactor state |

---

## Structure (Module Compliance)

**1487 Python files** across 9 packages · **1363/1487 compliant** (92%) · **124 over cap**

| Package | Files |
|---|---:|
| `src` | 820 |
| `pigeon_compiler` | 254 |
| `pigeon_brain` | 210 |
| `tests` | 136 |
| `streaming_layer` | 21 |
| `(root)` | 18 |
| `scripts` | 18 |
| `client` | 8 |
| `vscode-extension` | 2 |

### Over-Cap Files (>200 lines)

| File | Lines | Severity |
|---|---:|---|
| `src/tc_profile_seq001_v001.py` | 1585 | 🔴 CRIT |
| `src/tc_sim_seq001_v001.py` | 1339 | 🔴 CRIT |
| `src/profile_chat_server_seq001_v001.py` | 1280 | 🔴 CRIT |
| `autonomous_dev_stress_test.py` | 999 | 🔴 CRIT |
| `src/profile_renderer_seq001_v001.py` | 925 | 🔴 CRIT |
| `src/escalation_engine_seq001_v001.py` | 908 | 🔴 CRIT |
| `vscode-extension/classify_bridge.py` | 877 | 🔴 CRIT |
| `src/module_identity_seq001_v001.py` | 836 | 🔴 CRIT |
| `src/engagement_hooks_seq001_v001.py` | 823 | 🔴 CRIT |
| `src/vitals_renderer_seq001_v001.py` | 783 | 🔴 CRIT |
| `client/os_hook.py` | 736 | 🔴 CRIT |
| `src/tc_gemini_seq001_v001.py` | 736 | 🔴 CRIT |
| `_run_smart_rename.py` | 730 | 🔴 CRIT |
| `_build_organism_health.py` | 728 | 🔴 CRIT |
| `src/push_snapshot_seq001_v001.py` | 667 | 🔴 CRIT |
| `src/环w_pc_s025_v003_d0330_读唤任_λπ.py` | 663 | 🔴 CRIT |
| `src/entropy_shedding_seq001_v001.py` | 650 | 🔴 CRIT |
| `src/push_baseline_seq001_v001.py` | 641 | 🔴 CRIT |
| `src/codebase_transmuter_seq001_v001.py` | 637 | 🔴 CRIT |
| `pigeon_brain/flow/算f_ps_s014_v006_d0404_译改名踪_λNU_βoc.py` | 636 | 🔴 CRIT |
| ... | +104 more | |

---

## Circulation (Dependency Health)

**605/630 alive** · 25 clots · 50 arteries · avg vein health: 0.51 · 938 edges

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
| `classify_bridge` | 0.6 | orphan_no_importers, unused_exports:1, oversize:877 |
| `逆f_ba_bp_s005_v003_d0328_λR` | 0.45 | orphan_no_importers, unused_exports:1 |
| `学f_ll_cu_s006_v003_d0327_λγ` | 0.45 | orphan_no_importers, unused_exports:1 |
| `算f_ps_ca_s009_v002_d0327_λS` | 0.45 | orphan_no_importers, unused_exports:1 |
| `预p_pr_co_s001_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `f_he_s009_v005_d0401_改名册追跑_λA` | 0.45 | orphan_no_importers, unused_exports:1 |
| `正f_cmp_ah_s008_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `f_he_gf_s002_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `批编f_rbc_ma_s001_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `bug_profiles` | 0.45 | orphan_no_importers, unused_exports:1 |
| `.operator_stats_seq008_v010_d0331__persi_artifact_detection_seq003_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `u_uah_s007_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `隐p_un_di_s002_v003_d0322_λ7` | 0.45 | orphan_no_importers, unused_exports:1 |
| `u_pe_s024_v002_d0402_λC_block_builder_seq013_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `u_pj_s019_v002_d0402_λC_build_snapshot_decomposed_seq012_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `修f_sf_aaif_s011_v002_d0329_λH` | 0.45 | orphan_no_importers, unused_exports:1 |
| `修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_apply_import_fixes_seq012_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `思f_cr_ac_s007_v002_d0322_λ7` | 0.45 | orphan_no_importers, unused_exports:1 |
| `控f_ost_ad_s003_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `推w_dp_bch_s010_v001` | 0.45 | orphan_no_importers, unused_exports:1 |

---

## Hot Modules (Cognitive Load)

**66 modules tracked**

| Module | Avg Hesitation | Avg WPM | Samples | Dominant State |
|---|---:|---:|---:|---|
| `query_memory` | 0.000 | 0 | 0 | ? |
| `prompt_recon` | 0.000 | 0 | 0 | ? |
| `training_writer` | 0.000 | 0 | 0 | ? |
| `confidence_scorer` | 0.000 | 0 | 0 | ? |
| `timestamp_utils` | 0.000 | 0 | 0 | ? |
| `intent_simulator` | 0.000 | 0 | 0 | ? |
| `bug_profiles` | 0.000 | 0 | 0 | ? |
| `escalation_engine` | 0.000 | 0 | 0 | ? |
| `unified_signal` | 0.000 | 0 | 0 | ? |
| `git_plugin_main_orchestrator` | 0.000 | 0 | 0 | ? |
| `虚f_mc` | 0.000 | 0 | 0 | ? |
| `thought_completion` | 0.000 | 0 | 0 | ? |
| `module_identity` | 0.000 | 0 | 0 | ? |
| `audit_loops` | 0.000 | 0 | 0 | ? |
| `keystroke_live.jsonl` | 0.000 | 0 | 0 | ? |

---

## Rework Surface (AI Response Quality)

**200 responses scored** · avg rework score: 0.08

| Verdict | Count | % |
|---|---:|---:|
| ok | 165 | 82% |
| partial | 31 | 16% |
| miss | 4 | 2% |

### Reworked Responses (35)

| Time | Score | Del% | Query Hint |
|---|---:|---:|---|
| 2h ago | 0.30 | 27% | bg:BUG_PROFILES.md |
| 2h ago | 0.30 | 27% | bg:BUG_PROFILES.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 2h ago | 0.30 | 27% | bg:copilot-instructions.md |
| 1h ago | 0.30 | 27% | bg:copilot-instructions.md |

---

## Prompt Consolidation

**752 prompts** · 343 rewrites · 581 deleted words

### Intent Distribution

| Intent | Count | % |
|---|---:|---:|
| unknown | 251 | 33% |
| debugging | 130 | 17% |
| exploring | 127 | 17% |
| testing | 94 | 12% |
| building | 91 | 12% |
| restructuring | 22 | 3% |
| meta | 17 | 2% |
| continuing | 12 | 2% |
| shipping | 5 | 1% |
| documenting | 1 | 0% |
| file_wake | 1 | 0% |
| file_chat | 1 | 0% |

### Cognitive State Distribution

| State | Count | % |
|---|---:|---:|
| unknown | 752 | 100% |

### Unsaid Words (most deleted)

| Word | Times Deleted |
|---|---:|
| the | 7 |
| le | 5 |
| no | 5 |
| in | 5 |
| ps | 4 |
| co | 4 |
| to | 4 |
| er | 4 |
| ma | 4 |
| d\ | 4 |
| rs | 4 |
| and | 4 |
| ro | 4 |
| hi | 4 |
| aw | 4 |

---

## Push Cycle

| Metric | Value |
|---|---|
| Total Cycles | 20 |
| Last Commit | `46867e94` |
| Last Sync Score | 0.016 |
| Journal Line | 687 |
| Updated | 21h ago |

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
