# ORGANISM HEALTH — keystroke-telemetry

*Auto-generated 2026-04-09 20:03 UTC · 2511 Python files tracked · 453 prompts analyzed*

**This document is the organism. Every data pipeline that flows through this codebase is measured here. If it's not flowing, it's dying.**

---

## Vitals

| Metric | Value | Baseline |
|---|---|---|
| Cognitive State | **debugging** | — |
| WPM (latest) | 0.0 | ? |
| Deletion Ratio | 1.7% | ? |
| Prompts Analyzed | 453 | — |
| Session Message | #118 | — |
| Last Active | 5m ago (🟢) | — |
| Reactor Fires | 524 | — |

---

## Blood Flow (Data Pipelines)

| Pipeline | Entries | Size | Freshness | Role |
|---|---:|---:|---|---|
| prompt_journal | 453 | 481,350 | 🟢 5m ago | Enriched prompts |
| chat_compositions | 4195 | 6.1M | 🟢 5m ago | Keystroke compositions |
| edit_pairs | 105 | 45,361 | 🟡 16h ago | Prompt → file pairings |
| push_cycles | 17 | 63,792 | 🔴 5d ago | Push cycle reports |
| os_keystrokes | 152512 | 33.8M | 🟢 5m ago | OS-level keystrokes |
| keystroke_live | 14499 | 4.2M | 🟢 0s ago | Live keystroke stream |
| rework_log | 200 | 48,089 | 🟢 42s ago | AI answer quality |
| file_heat_map | 60 | 5,778 | 🟢 42s ago | Cognitive load per module |
| file_profiles | 254 | 223,585 | 🔴 5d ago | Module consciousness |
| pigeon_registry | 633 | 107,619 | 🟢 50s ago | Module registry |
| execution_deaths | 10 | 2,735 | 🔴 13d ago | Electron failures |
| context_veins | 7 | 91,345 | 🔴 7d ago | Vein/clot health |
| mutation_scores | 6 | 6,147 | 🔴 5d ago | Prompt mutation correlation |
| task_queue | 0 | 19 | 🔴 8d ago | Copilot task queue |
| push_cycle_state | 6 | 197 | 🔴 5d ago | Push cycle state |
| reactor_state | 3 | 17,841 | 🟢 41s ago | Reactor state |

---

## Structure (Module Compliance)

**2511 Python files** across 9 packages · **2303/2511 compliant** (92%) · **208 over cap**

| Package | Files |
|---|---:|
| `build` | 1773 |
| `src` | 377 |
| `pigeon_compiler` | 166 |
| `pigeon_brain` | 111 |
| `(root)` | 46 |
| `streaming_layer` | 21 |
| `tests` | 8 |
| `client` | 7 |
| `vscode-extension` | 2 |

### Over-Cap Files (>200 lines)

| File | Lines | Severity |
|---|---:|---|
| `pigeon_compiler/git_plugin.py` | 1547 | 🔴 CRIT |
| `src/层w_sl_s007_v003_d0317_读唤任_λΠ.py` | 1142 | 🔴 CRIT |
| `pigeon_compiler/rename_engine/谱建f_mb_s007_v003_d0314_观重箱重拆_λD.py` | 1017 | 🔴 CRIT |
| `autonomous_dev_stress_test.py` | 999 | 🔴 CRIT |
| `src/管w_cpm_s020_v005_d0404_缩分话_λNU_βoc.py` | 925 | 🔴 CRIT |
| `build/numerical/pigeon_compiler/git_plugin.py` | 919 | 🔴 CRIT |
| `src/profile_renderer.py` | 893 | 🔴 CRIT |
| `vscode-extension/classify_bridge.py` | 877 | 🔴 CRIT |
| `src/escalation_engine.py` | 876 | 🔴 CRIT |
| `src/tc_sim.py` | 828 | 🔴 CRIT |
| `src/module_identity.py` | 813 | 🔴 CRIT |
| `build/numerical/src/层w_sl_s007_v003_d0317_读唤任_λΠ.py` | 809 | 🔴 CRIT |
| `src/u_pj_s019_v003_d0404_λNU_βoc.py` | 799 | 🔴 CRIT |
| `build/compressed/src/streaming_layer_seq007_v003_d0317__monolithic_live_streaming_interface_for_lc_pulse_telemetry_prompt.py` | 791 | 🔴 CRIT |
| `build/numerical/pigeon_compiler/rename_engine/谱建f_mb_s007_v003_d0314_观重箱重拆_λD.py` | 782 | 🔴 CRIT |
| `build/compressed/pigeon_compiler/rename_engine/manifest_builder_seq007_v003_d0314__generate_living_manifest_md_per_lc_desc_upgrade.py` | 752 | 🔴 CRIT |
| `_run_smart_rename.py` | 730 | 🔴 CRIT |
| `src/engagement_hooks.py` | 723 | 🔴 CRIT |
| `client/os_hook.py` | 718 | 🔴 CRIT |
| `src/tc_profile.py` | 712 | 🔴 CRIT |
| ... | +188 more | |

---

## Circulation (Dependency Health)

**133/137 alive** · 4 clots · 21 arteries · avg vein health: 0.53 · 260 edges

### Critical Arteries (do NOT break)

| Module | In-Degree | Vein Score |
|---|---:|---:|
| `compliance` | 7 | 1.0 |
| `drift` | 5 | 1.0 |
| `cognitive_reactor` | 12 | 1.0 |
| `copilot_prompt_manager` | 11 | 1.0 |
| `streaming_layer` | 16 | 1.0 |
| `graph_extractor` | 5 | 0.93 |
| `graph_heat_map` | 5 | 0.93 |
| `compliance_seq008_audit_decomposed` | 9 | 0.93 |
| `source_slicer` | 5 | 0.9 |
| `unsaid` | 4 | 0.89 |

### Clots (dead/bloated)

| Module | Score | Signals |
|---|---:|---|
| `aim_utils` | 0.45 | orphan_no_importers, unused_exports:1 |
| `press_release_gen_constants_seq001_v001` | 0.45 | orphan_no_importers, unused_exports:1 |
| `adapter` | 0.45 | orphan_no_importers, unused_exports:1 |
| `query_memory` | 0.4 | dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory |

---

## Hot Modules (Cognitive Load)

**60 modules tracked**

| Module | Avg Hesitation | Avg WPM | Samples | Dominant State |
|---|---:|---:|---:|---|
| `rework_detector` | 0.000 | 0 | 0 | ? |
| `file_consciousness` | 0.000 | 0 | 0 | ? |
| `dynamic_prompt` | 0.000 | 0 | 0 | ? |
| `operator_stats` | 0.000 | 0 | 0 | ? |
| `prompt_journal` | 0.000 | 0 | 0 | ? |
| `prompt_recon` | 0.000 | 0 | 0 | ? |
| `copilot_prompt_manager` | 0.000 | 0 | 0 | ? |
| `pulse_harvest` | 0.000 | 0 | 0 | ? |
| `mutation_scorer` | 0.000 | 0 | 0 | ? |
| `query_memory` | 0.000 | 0 | 0 | ? |
| `self_fix` | 0.000 | 0 | 0 | ? |
| `timestamp_utils` | 0.000 | 0 | 0 | ? |
| `context_budget` | 0.000 | 0 | 0 | ? |
| `prompt_enricher` | 0.000 | 0 | 0 | ? |
| `cognitive_reactor` | 0.000 | 0 | 0 | ? |

---

## Rework Surface (AI Response Quality)

**200 responses scored** · avg rework score: 0.12

| Verdict | Count | % |
|---|---:|---:|
| ok | 158 | 79% |
| miss | 35 | 18% |
| partial | 7 | 4% |

### Reworked Responses (134)

| Time | Score | Del% | Query Hint |
|---|---:|---:|---|
| 30m ago | 0.19 | 7% | bg:sim_memory.json |
| 29m ago | 0.19 | 7% | bg:prompt_journal.jsonl |
| 28m ago | 0.19 | 7% | bg:prompt_journal.jsonl |
| 25m ago | 0.19 | 7% | bg:prompt_journal.jsonl |
| 23m ago | 0.19 | 7% | bg:prompt_journal.jsonl |
| 6m ago | 0.01 | 2% | bg:prompt_journal.jsonl |
| 2m ago | 0.01 | 2% | bg:prompt_journal.jsonl |
| 2m ago | 0.01 | 2% | bg:prompt_journal.jsonl |
| 1m ago | 0.01 | 2% | bg:prompt_journal.jsonl |
| 50s ago | 0.01 | 2% | bg:prompt_journal.jsonl |

---

## Prompt Consolidation

**453 prompts** · 227 rewrites · 389 deleted words

### Intent Distribution

| Intent | Count | % |
|---|---:|---:|
| unknown | 157 | 35% |
| debugging | 75 | 17% |
| building | 71 | 16% |
| exploring | 70 | 15% |
| testing | 58 | 13% |
| restructuring | 15 | 3% |
| continuing | 3 | 1% |
| shipping | 3 | 1% |
| documenting | 1 | 0% |

### Cognitive State Distribution

| State | Count | % |
|---|---:|---:|
| unknown | 453 | 100% |

### Unsaid Words (most deleted)

| Word | Times Deleted |
|---|---:|
| no | 5 |
| to | 4 |
| and | 4 |
| ps | 3 |
| er | 3 |
| fi | 3 |
| d\ | 3 |
| rs | 3 |
| ro | 3 |
| in | 3 |
| ot | 3 |
| the | 3 |
| hi | 3 |
| 00 | 3 |
| can we find a way to s | 3 |

---

## Push Cycle

| Metric | Value |
|---|---|
| Total Cycles | 17 |
| Last Commit | `5e29260` |
| Last Sync Score | 0.7 |
| Journal Line | 309 |
| Updated | 5d ago |

---

## Task Queue

*Queue empty.*

---

## Death Log (Execution Failures)

**10 deaths logged**

| Module | Cause | Severity | Time |
|---|---|---:|---|
| `plan_parser` | exception | high | 17d ago |
| `dynamic_prompt` | exception | high | 17d ago |
| `copilot_prompt_manager_seq020_block_utils` | loop | low | 17d ago |
| `import_tracer` | exception | high | 17d ago |
| `unsaid` | loop | high | 13d ago |
| `failure_detector` | timeout | high | 13d ago |
| `graph_heat_map` | timeout | high | 13d ago |
| `backward` | stale_import | critical | 13d ago |
| `graph_heat_map` | loop | low | 13d ago |
| `file_consciousness` | stale_import | critical | 13d ago |

---


*Regenerate: `py _build_organism_health.py` · Wire into `git_plugin.py` post-commit for auto-refresh.*
