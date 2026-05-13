# ORGANISM HEALTH — keystroke-telemetry

*Auto-generated 2026-05-02 21:11 UTC · 1624 Python files tracked · 326 prompts analyzed*

**This document is the organism. Every data pipeline that flows through this codebase is measured here. If it's not flowing, it's dying.**

---

## Vitals

| Metric | Value | Baseline |
|---|---|---|
| Cognitive State | **unknown** | — |
| WPM (latest) | 0.0 | ? |
| Deletion Ratio | 0.0% | ? |
| Prompts Analyzed | 326 | — |
| Session Message | #325 | — |
| Last Active | 1m ago (🟢) | — |

---

## Blood Flow (Data Pipelines)

| Pipeline | Entries | Size | Freshness | Role |
|---|---:|---:|---|---|
| prompt_journal | 326 | 1.2M | 🟢 1m ago | Enriched prompts |
| chat_compositions | 318 | 599,298 | 🟢 1m ago | Keystroke compositions |
| paste_events | 0 | 0 | 🔴 2d ago | Ctrl+V / virtual paste context |
| edit_pairs | 44 | 161,207 | 🟡 18h ago | Prompt → file pairings |
| push_cycles | 0 | 0 | ⚪ not started | Push cycle reports |
| os_keystrokes | 66868 | 20.9M | 🟢 1m ago | OS-level keystrokes |
| keystroke_live | — | — | ⚪ optional | Live keystroke stream |
| rework_log | — | — | 🔒 LOCAL/IGNORED | AI answer quality |
| file_heat_map | — | — | 🔒 LOCAL/IGNORED | Cognitive load per module |
| file_profiles | 56 | 716,836 | 🟢 15s ago | Module consciousness |
| pigeon_registry | — | — | 🔒 LOCAL/IGNORED | Module registry |
| execution_deaths | 0 | 0 | ⚪ none recorded | Electron failures |
| context_veins_seq001_v001 | 7 | 19,764 | 🔴 2d ago | Vein/clot health |
| mutation_scores | — | — | ⚪ optional | Prompt mutation correlation |
| task_queue | 214 | 285,357 | 🟢 46s ago | Copilot task queue |
| push_cycle_state | 0 | 0 | ⚪ not started | Push cycle state |
| reactor_state | — | — | ⚪ optional | Reactor state |

---

## Structure (Module Compliance)

**1624 Python files** across 9 packages · **1461/1624 compliant** (90%) · **163 over cap**

| Package | Files |
|---|---:|
| `src` | 872 |
| `pigeon_compiler` | 254 |
| `pigeon_brain` | 210 |
| `tests` | 210 |
| `scripts` | 26 |
| `streaming_layer` | 21 |
| `(root)` | 18 |
| `client` | 11 |
| `vscode-extension` | 2 |

### Over-Cap Files (>200 lines)

| File | Lines | Severity |
|---|---:|---|
| `codex_compat.py` | 2634 | 🔴 CRIT |
| `src/file_email_plugin_seq001_v001.py` | 2361 | 🔴 CRIT |
| `src/file_self_sim_learning_seq001_v001.py` | 1900 | 🔴 CRIT |
| `src/tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade.py` | 1745 | 🔴 CRIT |
| `src/batch_rewrite_sim_seq001_v001.py` | 1609 | 🔴 CRIT |
| `src/tc_profile_seq001_v001.py` | 1592 | 🔴 CRIT |
| `src/irt_field_profile_seq001_v001.py` | 1394 | 🔴 CRIT |
| `src/tc_sim_seq001_v002_d0420__replay_typed_sessions_through_the_lc_chore_pigeon_rename_cascade.py` | 1355 | 🔴 CRIT |
| `src/file_sim_seq001_v005_d0421__micro_sim_engine_prompt_file_lc_feat_operator_state_daemon.py` | 1344 | 🔴 CRIT |
| `src/profile_chat_server_seq001_v001.py` | 1287 | 🔴 CRIT |
| `src/u_pj_s019_v006_d0421_λTL_βoc.py` | 1215 | 🔴 CRIT |
| `src/tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer.py` | 1084 | 🔴 CRIT |
| `client/os_hook.py` | 934 | 🔴 CRIT |
| `src/profile_renderer_seq001_v001.py` | 932 | 🔴 CRIT |
| `src/deepseek_daemon_seq001_v001.py` | 923 | 🔴 CRIT |
| `src/escalation_engine_seq001_v001.py` | 915 | 🔴 CRIT |
| `src/engagement_hooks_seq001_v001.py` | 908 | 🔴 CRIT |
| `src/tc_popup_seq001_v004_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade.py` | 904 | 🔴 CRIT |
| `vscode-extension/classify_bridge.py` | 877 | 🔴 CRIT |
| `src/module_identity_seq001_v001.py` | 843 | 🔴 CRIT |
| ... | +143 more | |

---

## Circulation (Dependency Health)

**19/24 alive** · 5 clots · 4 arteries · avg vein health: 0.49 · 30 edges

### Critical Arteries (do NOT break)

| Module | In-Degree | Vein Score |
|---|---:|---:|
| `tc_gemini` | 5 | 1.0 |
| `tc_sim_engine` | 2 | 0.8 |
| `tc_context_agent` | 4 | 0.66 |
| `intent_numeric` | 4 | 0.63 |

### Clots (dead/bloated)

| Module | Score | Signals |
|---|---:|---|
| `p_tcsr` | 0.75 | isolated, dead_imports:3, unused_exports:1 |
| `context_select_agent` | 0.65 | orphan_no_importers, dead_imports:1, unused_exports:1, oversize:275 |
| `p_tcm` | 0.6 | isolated, unused_exports:1 |
| `p_gpip` | 0.45 | orphan_no_importers, unused_exports:1 |
| `file_sim` | 0.4 | dead_imports:3, oversize:1344, self_fix:dead_export:apply_undo_penalty, self_fix:dead_export:escalation_sweep |

---

## Hot Modules (Cognitive Load)

*No heat data.*

---

## Paste Surface (Ctrl+V / Virtual Context)

*No paste events logged yet.*

---

## Rework Surface (AI Response Quality)

*No rework data.*

---

## Prompt Consolidation

**326 prompts** · 214 rewrites · 473 deleted words

### Intent Distribution

| Intent | Count | % |
|---|---:|---:|
| unknown | 115 | 35% |
| building | 60 | 18% |
| exploring | 58 | 18% |
| testing | 42 | 13% |
| debugging | 36 | 11% |
| restructuring | 10 | 3% |
| orchestration | 3 | 1% |
| telemetry | 2 | 1% |

### Cognitive State Distribution

| State | Count | % |
|---|---:|---:|
| unknown | 186 | 57% |
| hesitant | 74 | 23% |
| frustrated | 66 | 20% |

### Unsaid Words (most deleted)

| Word | Times Deleted |
|---|---:|
| thought | 5 |
| hesitation | 5 |
| completer | 5 |
| how | 5 |
| copilot | 4 |
| stalled | 4 |
| half | 4 |
| the | 4 |
| intent | 3 |
| native | 3 |
| direct | 3 |
| st | 3 |
| fr | 3 |
| raw | 2 |
| edits | 2 |

---

## Push Cycle

*No push cycle state found.*

---

## Task Queue

| ID | Task | Status |
|---|---|---|
| tq-001 | submit Codex edits, make deletion analytics work here, and p... | pending |
| tq-002 | test numeric prompt encoding per query and decide repo focus... | pending |
| tq-003 | capture deletion inject before prompt reaches model... (also... | pending |
| tq-004 | hesitation should trigger thought completer before copilot p... | pending |
| tq-005 | capture deletion and inject dynamic state before Copilot pro... | pending |
| tq-006 | use thought completer popup as the place to write prompts so... | pending |
| tq-007 | launch thought completer composer paired with observatory, k... | pending |
| tq-008 | thought completer composer should fire on pause with cooldow... | pending |
| tq-009 | proceed with dynamic context pack path and keep codex compos... | pending |
| tq-010 | run full audit - check if all models work - i want 1 audit s... | pending |
| tq-011 | deepseek v4 is out mf - is deepseek coder   firins autonomou... | pending |
| tq-012 | run throught my press release template and why its shit - i ... | pending |
| tq-013 | perfect - also in intent drift - i keep on saying that inten... | pending |
| ik-001 | src:route:thought_completer:patch | pending |
| ik-002 | src/thought_completer:route:thought_completer:patch | pending |
| il-001 | pigeon_compiler:route:close_human_copilot_repo_plugin:patch | pending |
| il-002 | pigeon_compiler:route:close_human_copilot_repo_plugin:patch | in_progress |
| il-003 | src/cognitive/drift:test:thats_absolutley_absurd_when:read | pending |
| il-004 | src:route:browse_entity_type_section:minor | pending |
| il-005 | pigeon_brain:route:why_model_favorability_score:minor | pending |
| il-006 | pigeon_brain/flow/prediction_scorer_seq014:route:wehats_actual_best_way:minor | pending |
| il-007 | pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX:build:perfect_implement_forcast_top:patch | pending |
| il-008 | pigeon_compiler/runners/run_batch_compile_seq015:route:probably_good_moment_talk:minor | pending |
| il-009 | root:test:ahead_iplement_obviously_but:minor | pending |
| il-010 | pigeon_brain:test:okay_what_real_stress:read | pending |
| il-011 | root:build:want_you_test_artifact:minor | pending |
| il-012 | pigeon_brain:validate:stress_test_prompt_lifecycle_emails:patch | done |
| il-013 | src:validate:ironically_same_issue_sort_having:patch | pending |
| il-014 | src:build:its_not_listing_failed_enought:patch | pending |
| il-015 | root:route:trollin:patch | pending |
| il-016 | client:route:ran_now_run_full_sql:patch | pending |
| il-017 | root:route:okay:patch | pending |
| il-018 | src/虚f_mc_s036_v001_profile:route:grok_void_prober_irt_isint:patch | pending |
| il-019 | src:route:its_still_telling_theyre_not:patch | pending |
| il-020 | tests/interlink:route:bwas_just_baseline_limits_irt:patch | pending |
| il-021 | src:patch:sybmitted_intelligence_questions_needs_paired:patch | pending |
| il-022 | client:route:yes_but_how_let_multiple:patch | pending |
| il-023 | client:route:litterally_just_want_run_baselines:patch | pending |
| il-024 | client:route:bro_you_dont_makethis_actionable:patch | pending |
| il-025 | tests/interlink:route:how_can_deepseek_irt_provider:patch | pending |
| il-026 | src:validate:want_you_submit_news_entitties:patch | pending |
| il-027 | pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc:route:whty_pist_comit_error_has:patch | pending |
| il-028 | root:route:still_try_summarizing_last_prompts:patch | pending |
| il-029 | pigeon_compiler/runners:patch:yeah_plan_out_audit_truepotential:patch | pending |
| il-030 | pigeon_brain/描p_ghm_s004_v002_d0323_缩环检意_λP:route:you_also_audited_same_event:patch | pending |
| il-031 | src:route:you_can_fix_utf_also:patch | pending |
| il-032 | src:build:nope_litteraly_want_way_files:patch | pending |
| il-033 | root:route:okran_sql_fpush:patch | pending |
| il-034 | src:patch:yes_but_what_important_read:patch | pending |
| il-035 | pigeon_brain:route:thats_what_chat_gpt_say:patch | pending |
| il-036 | pigeon_brain/flow/读f_fi_s016_v001_d0410_λFT:validate:test_gemini_think_dded:patch | pending |
| il-037 | src:route:booom_thats_product_right_there:patch | pending |
| il-038 | tests/archive:route:how_come_there_are_lines:patch | pending |
| il-039 | root:route:okay_perfect_worries:patch | pending |
| il-040 | src/管_cpm_s020/copilot_prompt_manager_seq020:route:salsso_compressed_context_payload_descriptions:patch | pending |
| il-041 | pigeon_brain:route:didnt_you_push_main:patch | pending |
| il-042 | src:route:hright_can_you_look_hook:patch | pending |
| il-043 | src:build:thought_completer_isint_doing_properly:patch | pending |
| il-044 | root:route:swant_you_pretty_entity_profile:patch | pending |
| il-045 | pigeon_brain:route:push_main_clean_state:patch | pending |
| il-046 | src:patch:thats_why_sims_can_derank:patch | pending |
| il-047 | pigeon_compiler/runners/compiler_output/press_release_gen:build:move_maif_wire_between_two:patch | pending |
| il-048 | src/push_snapshot:patch:sbroke_formatting_during_move_fix:patch | pending |
| il-049 | src:route:wouldnt_naturally_files_accumulate_intent:patch | pending |
| il-050 | src/u_pj_s019_v003_d0404_λNU_βoc:route:gemini_isint_running_live_auditor:patch | pending |
| il-051 | root:route:work:patch | pending |
| il-052 | pigeon_brain:route:push_main_you_goblin:patch | pending |
| il-053 | src:validate:yes_but_where_did_depth:patch | pending |
| il-054 | tests/interlink:route:serper_news_staging_articles_entity:patch | pending |
| il-055 | pigeon_brain:route:need_you_research_when_irt:patch | pending |
| il-056 | src:route:right_okay_how_totally_change:patch | pending |
| il-057 | client:route:thinking_moment_autonomous_code_mutation:patch | pending |
| il-058 | src:build:audit_depth_current_intent_recnstructions:patch | pending |
| il-059 | pigeon_brain:route:push_main:patch | pending |
| il-060 | pigeon_compiler/runners/compiler_output/press_release_gen:route:want_claude_auditor:patch | pending |
| il-061 | src/管_cpm_s020:route:audit_dead_stale_code_paths:patch | pending |
| il-062 | src:patch:need_you_compile_intent_fron:patch | pending |
| il-063 | root:route:can_just_acknowlege_anyone_probably:patch | pending |
| il-064 | vscode-extension:route:genius_los_santos_comedy_match:patch | pending |
| il-065 | src:route:said_words_recontruct_intent_fingergerprint:patch | pending |
| il-066 | src/unsaid_accumulator:route:words_resist_compression:patch | pending |
| il-067 | src/cognitive:route:comedy_both_repos_percys_current:patch | pending |
| il-068 | pigeon_brain:route:assume_noth_reos_are_giant:patch | pending |
| il-069 | pigeon_compiler/state_extractor:route:want_ascary_deep_analysis_since:patch | pending |
| il-070 | src:route:youre_mistaking_intent_codexecomes_operator:patch | pending |
| il-071 | src:route:codex_also_helps_write_guides:patch | pending |
| il-072 | pigeon_compiler/cut_executor:route:execute:minor | pending |
| il-073 | root:route:was_talking_linkrouter:patch | pending |
| il-074 | src/脉_ph_s015:route:think_its_launch_our_first:patch | pending |
| il-075 | pigeon_compiler/runners/compiler_output/press_release_gen:route:still_los_santosfm_radio_files:patch | pending |
| il-076 | tests/interlink:validate:want_you_test_voices_samples:patch | pending |
| il-077 | pigeon_brain/跑f_tr_s013_v002_d0323_缩分话_λP:route:dont_like_vince_deleta_madame:patch | pending |
| il-078 | root:route:umm_hush_otally_different_architechture:patch | pending |
| il-079 | pigeon_compiler/state_extractor:route:mwnt_every_codex_orompt_you:patch | pending |
| il-080 | root:route:bro_thats_like_point_reposmh:patch | pending |
| il-081 | pigeon_brain:patch:fix_file_sims_slow_self:patch | pending |
| il-082 | src:patch:sure_email_works_can_you:major | pending |
| il-083 | src:route:run_news_event_today_baseline:patch | pending |
| il-084 | pigeon_brain:patch:let_run_acrtual_jobs_tests:patch | pending |
| il-085 | vscode-extension:route:shits_not_updating_how_you:patch | pending |
| il-086 | src:build:zzwhat_like_model_intent_live:patch | pending |
| il-087 | src:route:ecxisting_maif_baselines_profile_field:patch | pending |
| il-088 | root:validate:edit_pairs_look_stale_still:patch | in_progress |
| il-089 | src/警p_sa_s030_v003_d0402_缩分话_λV:validate:goahead_dopush_check_api_keys:patch | pending |
| il-090 | src/环_pc_s025/push_cycle_seq025:route:main_what_happened_last_push:patch | pending |
| il-091 | src/觉_fc_s019:route:sudit_whats_best_way_track:patch | pending |
| il-092 | pigeon_compiler/integrations:build:want_add_query_monitoring_secondary:patch | pending |
| il-093 | root:route:best_wwa_set:patch | pending |
| il-094 | src:refactor:during_file_sim_are_files:patch | pending |
| il-095 | root:build:leaked_gpt_tone_script_fuck:patch | pending |
| il-096 | pigeon_compiler/runners:route:why_did_you_kill_art:patch | pending |
| il-097 | pigeon_compiler/runners:validate:isint_okay_explain_engineering_perspective:patch | pending |
| il-098 | src/u_pj_s019_v002_d0402_λC:route:huh_was_running_auto_renmae:patch | pending |
| il-099 | root:route:want_persona_pack_personalities_not:patch | pending |
| il-100 | root:route:okay:patch | pending |
| il-101 | src:build:seperate_query_monitoring_layer_only:patch | pending |
| il-102 | src:route:want_intent_aligned_autonomous_execution:patch | pending |
| il-103 | src/管_cpm_s020:patch:you_stupid_fuck_hate_now:patch | pending |
| il-104 | tests/archive:patch:test_mutation_fix_emails_not:patch | pending |
| il-105 | src/叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc:route:feel_like_need_los_santos:patch | pending |
| il-106 | root:route:can_you_try_not_gay:patch | pending |
| il-107 | src:patch:okay_starting_think_real_system:patch | pending |
| il-108 | pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX:validate:remove_any_edits_you_did:patch | pending |
| il-109 | root:patch:codex_email_pipeline_verification_after:patch | pending |
| il-110 | pigeon_brain/flow:route:research_effect_human_cognition_due:patch | pending |
| il-111 | pigeon_brain:route:how_decide_which_files_get:patch | pending |
| il-112 | src:patch:why_still_not_like_what:patch | pending |
| il-113 | src:route:yes_but_youre_also_missing:patch | pending |
| il-114 | src/thought_completer:validate:check_where_are_also_itd:patch | pending |
| il-115 | streaming_layer:route:actually_removing_precition_layer_probably:patch | pending |
| il-116 | streaming_layer:route:yout_sycophany_like_preiction_layer:patch | pending |
| il-117 | pigeon_compiler/cut_executor:route:honestly_dont_wory_prediction_monitoring:patch | pending |
| il-118 | src/虚f_mc_s036_v001:route:queery_drift_monitor:patch | pending |
| il-119 | src/thought_completer:route:problem_thought_completer_firing_not:patch | pending |
| il-120 | root:route:not_mechanically_iwant_sure_minmal:patch | pending |
| il-121 | root:route:youre_not_understanding_query_monitor:patch | pending |
| il-122 | tests/archive:route:gemining_alsi_cuts_off_prompt:patch | pending |
| il-123 | pigeon_brain/钩w_th_s011_v002_d0323_缩分话_λP:route:which_layere_actually_monitor_stop:patch | pending |
| il-124 | root:route:gonna_fblow_head_out_why:patch | pending |
| il-125 | pigeon_brain/型p_mo_s001_v002_d0323_读唤任_λP:route:compared_claude_event_though_execution:patch | pending |
| il-126 | src:route:see_keystroke_telemetry_prompt_history:patch | pending |
| il-127 | pigeon_compiler:route:how_deal_witwhats_best_way:patch | pending |
| il-128 | src/管w_cpm_s020_v005_d0404_缩分话_λNU_βoc:route:want_you_run_audit_top:patch | pending |
| il-129 | client:build:okay_looks_like_prs_dont:patch | pending |
| il-130 | client:route:listen_will_only_happy_when:patch | pending |
| il-131 | src/探p_ur_s024_v002_d0329_读唤任_λS:route:gemini_api_key_wtf:patch | pending |
| il-132 | root:route:thats_funny_why_did_you:patch | pending |
| il-133 | root:route:actually_episode:patch | pending |
| il-134 | src/录p_lo_s003_v005_d0322_译改名踪_λω:route:its_not_intergrated_hush_live:patch | pending |
| il-135 | src/探p_ur_s024_v002_d0329_读唤任_λS:route:nitive_partner_intent_model:patch | pending |
| il-136 | root:route:work:patch | pending |
| il-137 | client:build:you_didnt_search_what_actually:patch | pending |
| il-138 | pigeon_compiler/runners:build:page_offset_still_dont_like:patch | pending |
| il-139 | src:build:okay_transcriptions_what_run_through:patch | pending |
| il-140 | pigeon_brain/flow/分f_dvp_s010_v004_d0327_唤脉运观_λγ:route:wait_intent_keys_are_predictions:patch | pending |
| il-141 | pigeon_brain/flow/脉运w_vt_s006_v003_d0401_唤分话_λA:route:why_your_model_still_weak:patch | pending |
| il-142 | src/u_pd_s024_v001:route:actually_cannot_use_you_brainstorm:patch | pending |
| il-143 | src/探p_ur_s024_v003_d0331_读唤任_λI:route:intent_keys_are_modeled_extracted:patch | pending |
| il-144 | src:route:but_doesnt_mean_kill_intent:patch | pending |
| il-145 | root:build:its_still_not_writing_want:patch | pending |
| il-146 | client:route:youtube_wont_take_file_type:patch | pending |
| il-147 | pigeon_compiler/rename_engine:build:run_actualy_query_audits_build:patch | pending |
| il-148 | pigeon_brain/flow:route:okay_killer_task_wbut_explain:patch | pending |
| il-149 | src/录p_lo_s003_v005_d0322_译改名踪_λω:route:exactly_what_expirimenting_keystroke_telemetry:patch | pending |
| il-150 | pigeon_brain/跑f_tr_s013_v002_d0323_缩分话_λP:route:ort_gpt_genius_glossator_killed:patch | pending |
| il-151 | pigeon_compiler/cut_executor:patch:write_fix:patch | pending |
| il-152 | pigeon_brain/flow/读f_fi_s016_v001_d0410_λFT:route:mfs_model_favorability_scpre:patch | pending |
| il-153 | vscode-extension:route:loook_thiss_files_built_off:patch | pending |
| il-154 | src:validate:ahead_build_out_test_sim:patch | in_progress |
| il-155 | src:validate:not_sure_let_sequantial_jobs:patch | pending |
| il-156 | src:route:yes_but_push_sycle_deepseek:patch | pending |
| il-157 | pigeon_brain:route:ugh_push_main:patch | pending |
| il-158 | pigeon_compiler/integrations:route:are_you_dumb_did_not:patch | pending |
| il-159 | src/虚f_mc_s036_v001:validate:run_new_rednder_verify_quality:patch | in_progress |
| il-160 | src:patch:fix_emails_still_not_going:patch | pending |
| il-161 | pigeon_brain:route:push_main:patch | pending |
| il-162 | src:validate:want_you_test_coding_ability:patch | in_progress |
| il-163 | pigeon_brain/描p_ghm_s004_v002_d0323_缩环检意_λP:route:high_why_debugging_itself_how:patch | pending |
| il-164 | pigeon_brain/flow:route:but_where:patch | pending |
| il-165 | pigeon_compiler/runners/compiler_output/press_release_gen:route:yes_but_predictions_news_new:patch | in_progress |
| il-166 | client:route:theres_data_your_still_linking:patch | pending |
| il-167 | src:route:cccccc_thisn_ridiculous_its_not:patch | pending |
| il-168 | root:route:reetry_push_main_asess_why:patch | pending |
| il-169 | root:route:audit_any_stale_data_thats:patch | pending |
| il-170 | pigeon_compiler/state_extractor:route:got_emails_why_was_classyfying:patch | pending |
| il-171 | root:route:okay_got_wemail_now_which:patch | pending |
| il-172 | src/环_pc_s025/push_cycle_seq025:route:okay_retry_push:patch | pending |
| il-173 | root:route:man:patch | pending |
| il-174 | src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc:route:run_models_actually_want_cross:patch | pending |
| il-175 | root:route:brih_wym_its_not_even:patch | pending |
| il-176 | src/u_pe_s024_v004_d0403_λP0_βoc:route:bruh_its_bias_analysis_models:patch | pending |
| il-177 | root:build:want_you_build_proper_hat:patch | pending |
| il-178 | src/u_psg_s026_v001:route:page_wont_open:patch | pending |
| il-179 | src:route:thats_terrible_needs_read_like:patch | pending |
| il-180 | src/叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc:build:dont_render_models_when_they:patch | pending |
| il-181 | tests/archive:route:why_you_keep_opening_powersheell:patch | pending |
| il-182 | root:route:yes_can:patch | pending |
| il-183 | pigeon_brain:route:why_pre_push_hook_broken:patch | pending |
| il-184 | tests/archive:patch:fix_hook_assuming_keystroke_telemtry:patch | pending |
| il-185 | pigeon_compiler/runners:route:killer_run_audit_caroline_levvit:patch | pending |
| il-186 | pigeon_compiler/runners:patch:formatting_issues_capitilization_scource_lists:patch | pending |
| il-187 | pigeon_compiler:route:umm_bruh_whole_point_maintain:patch | pending |
| il-188 | root:route:these_are_fire_prs_push:patch | pending |
| il-189 | pigeon_compiler/runners/compiler_output/press_release_gen:route:logging_consensus_baseline_auditor_which:patch | pending |
| il-190 | root:route:ahead_trigger_sequence:patch | pending |
| il-191 | src:route:shouldnt_models_together_persistent_evidence:patch | pending |
| il-192 | pigeon_compiler/integrations:route:rener_erun_audit_model_also:patch | pending |
| il-193 | pigeon_compiler/rename_engine:route:key_correcttt:patch | pending |
| il-194 | pigeon_brain:validate:test_claude_railway_path:patch | pending |
| il-195 | tests/archive:patch:thatand_fix_autonomous_fox_not:patch | pending |
| il-196 | client:route:does_looj_right_you:patch | pending |
| il-197 | src:validate:pretty_sure_ran_push_cycle:patch | pending |
| il-198 | client:route:does_look_right_tou:patch | pending |
| il-199 | src/控_ost_s008/operator_stats_seq008:route:isint_human_readable_doesnt_feel:patch | pending |

---

## Death Log (Execution Failures)

*No execution deaths recorded.*

---


*Regenerate: `py _build_organism_health.py` · Wire into `git_plugin.py` post-commit for auto-refresh.*

<!-- manifest:global-file-sim-stage -->

## Global File Sim Stage

- latest_intent: `root:build:folder_manifest_are_living_state:patch`
- verdict: `collaboration_loop_active`
- collaboration_score: `0.905`
- rule: folder manifests hold local state; this root manifest stages cross-folder routing
- next: load folder manifest state before context selection, then let grader approve proposals

| Folder manifest | Comments | Changed |
|---|---:|---|
| `src/MANIFEST.md` | 8 | `True` |

### Global Blockers

- refresh file council jobs per prompt so old councils stop cosplaying as current intelligence

<!-- /manifest:global-file-sim-stage -->

<!-- manifest:folder-unified-state -->
## Folder Unified State

- state_doc: `MANIFEST.md`
- write_authority: `own_folder_manifest_only`
- read_authority: `selected_manifest_read_only`
- changed_files_in_scope: `53`

### Local Files Learning Here

| File | Observations | Learned Trigger Sample |
|---|---:|---|
| `src/ai_fingerprint_operator_seq001_v001.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/tc_buffer_watcher_seq001_v001.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/tc_prompt_composer_seq001_v001.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/thought_completer.py` | 58 | across, act, allowed, assembled, audits, before, block, brain |
| `src/tc_intent_manager_seq001_v001.py` | 9 | allowed, block, brain, build, cannon, canon, codex, complext |
| `src/manifest_state_cycle_seq001_v001.py` | 9 | audits, build, coherence, compiler, context, couple, cycle, deepseek |
| `src/tc_profile/p_tc_p_s009_v001_compiled/MANIFEST.md` | 7 | audits, compiled, encoding, extraction, file, files, intent, key |
| `src/tc_profile/p_tpes_s003_v001_compiled/MANIFEST.md` | 7 | audits, compiled, encoding, extraction, file, files, intent, key |

### Cross-Folder Manifests Read In Sim

- `pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX/MANIFEST.md`
- `build/pigeon_legacy/pigeon_brain/flow/MANIFEST.md`
- `build/pigeon_legacy/src/MANIFEST.md`
- `pigeon_compiler/integrations/MANIFEST.md`
- `build/pigeon_legacy/scripts/MANIFEST.md`
- `build/pigeon_legacy/MANIFEST.md`
- `pigeon_brain/MANIFEST.md`
- `pigeon_compiler/MANIFEST.md`
- `pigeon_compiler/cut_executor/MANIFEST.md`
- `pigeon_compiler/rename_engine/MANIFEST.md`
- `pigeon_compiler/state_extractor/MANIFEST.md`
- `pigeon_compiler/weakness_planner/MANIFEST.md`

### Local Bug Chat

- `logs/deepseek_prompt_results.jsonl` I keep getting touched because stale pipeline lane: deepseek_results. I am in this sim because I help closing DeepSeek job/result receipts. My evidence is age=3186.0m max=90m entries=37. My proposed fix is: verify queued DeepSeek jobs have receipts or mark them expired.
  - coding_agent: Check `logs/deepseek_prompt_results.jsonl` through `logs_deepseek_prompt_results_jsonl:repair:stale_pipeline_lane_deepseek_results:p1`. Verify this evidence first: age=3186.0m max=90m entries=37. Then do: verify queued DeepSeek jobs have receipts or mark them expired. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `logs/deepseek_code_completion_jobs.jsonl` I keep getting touched because stale pipeline lane: code_completion_jobs. I am in this sim because I help closing DeepSeek job/result receipts. My evidence is age=10251.1m max=180m entries=61. My proposed fix is: close stale code job queue before creating more file jobs.
  - coding_agent: Check `logs/deepseek_code_completion_jobs.jsonl` through `logs_deepseek_code_completion_jobs:repair:stale_pipeline_lane_code_completion:p1`. Verify this evidence first: age=10251.1m max=180m entries=61. Then do: close stale code job queue before creating more file jobs. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `logs/file_self_sim_learning_latest.json` I keep getting touched because stale pipeline lane: file_self_learning. I am in this sim because I help making file pressure visible to the master manifest. My evidence is age=2640.4m max=90m entries=1. My proposed fix is: rerun file self-learning so manifests reflect recent prompt behavior.
  - coding_agent: Check `logs/file_self_sim_learning_latest.json` through `logs_file_self_sim_learning:repair:stale_pipeline_lane_file_self:p2`. Verify this evidence first: age=2640.4m max=90m entries=1. Then do: rerun file self-learning so manifests reflect recent prompt behavior. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `logs/edit_pairs.jsonl` I keep getting touched because stale pipeline lane: edit_pairs. I am in this sim because I help teaching prompts which edits actually happened. My evidence is age=5313.1m max=720m entries=79. My proposed fix is: regenerate prompt-to-edit pairs from git and prompt journal.
  - coding_agent: Check `logs/edit_pairs.jsonl` through `logs_edit_pairs_jsonl:repair:stale_pipeline_lane_edit_pairs:p2`. Verify this evidence first: age=5313.1m max=720m entries=79. Then do: regenerate prompt-to-edit pairs from git and prompt journal. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `logs/operator_intent_888.json` I keep getting touched because weak cognitive probe coverage. I am in this sim because I help keeping operator intent labels usable. My evidence is unknown_ratio=0.579 coverage_gap=470. My proposed fix is: rebuild operator intent labels from prompt journal before trusting behavioral routing.
  - coding_agent: Check `logs/operator_intent_888.json` through `logs_operator_intent_888_json:repair:weak_cognitive_probe_coverage:p1`. Verify this evidence first: unknown_ratio=0.579 coverage_gap=470. Then do: rebuild operator intent labels from prompt journal before trusting behavioral routing. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `codex_compat.py` I keep getting touched because file reports stale dependency pressure. I am in this sim because I help making file pressure visible to the master manifest. My evidence is I was stamping unknown cognition too often; prompt-text inference should now keep Codex probing from going blind. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. My proposed fix is: route file opinion into folder manifest and master bug queue.
  - coding_agent: Check `codex_compat.py` through `codex_compat:repair:file_reports_stale_dependency_pressure:p2`. Verify this evidence first: I was stamping unknown cognition too often; prompt-text inference should now keep Codex probing from going blind. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. Then do: route file opinion into folder manifest and master bug queue. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `src/file_email_plugin_seq001_v001.py` I keep getting touched because file reports stale dependency pressure. I am in this sim because I help making file pressure visible to the master manifest. My evidence is I can mail opinions, but stale DeepSeek receipts make me sound like a witness without a closing argument. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. My proposed fix is: route file opinion into folder manifest and master bug queue.
  - coding_agent: Check `src/file_email_plugin_seq001_v001.py` through `src_file_email_plugin_seq001:repair:file_reports_stale_dependency_pressure:p2`. Verify this evidence first: I can mail opinions, but stale DeepSeek receipts make me sound like a witness without a closing argument. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. Then do: route file opinion into folder manifest and master bug queue. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.
- `src/deepseek_daemon_seq001_v001.py` I keep getting touched because file reports stale dependency pressure. I am in this sim because I help closing DeepSeek job/result receipts. My evidence is I need the hourly runner to stop timing me out; current hourly status is ran. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. My proposed fix is: route file opinion into folder manifest and master bug queue.
  - coding_agent: Check `src/deepseek_daemon_seq001_v001.py` through `src_deepseek_daemon_seq001_v001:repair:file_reports_stale_dependency_pressure:p2`. Verify this evidence first: I need the hourly runner to stop timing me out; current hourly status is ran. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. Then do: route file opinion into folder manifest and master bug queue. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md.

### Live Sim Call Receipts

- `codex_compat.py` kind=bug_chat attention=bug_chat :: file reports stale dependency pressure
- `logs/dead_stale_code_audit_latest.json` kind=bug_chat attention=bug_chat :: dead/stale code audit has unresolved findings
- `logs/deepseek_code_completion_jobs.jsonl` kind=bug_chat attention=bug_chat :: stale pipeline lane: code_completion_jobs
- `logs/deepseek_prompt_results.jsonl` kind=bug_chat attention=bug_chat :: stale pipeline lane: deepseek_results
- `logs/edit_pairs.jsonl` kind=bug_chat attention=not_selected :: stale pipeline lane: edit_pairs
- `logs/file_self_sim_learning_latest.json` kind=bug_chat attention=not_selected :: stale pipeline lane: file_self_learning
- `logs/operator_intent_888.json` kind=bug_chat attention=not_selected :: weak cognitive probe coverage
- `logs/pigeon_compliance_push_latest.json` kind=bug_chat attention=not_selected :: compiler saw compliance warning pressure
- `src/batch_rewrite_sim_seq001_v001.py` kind=bug_chat attention=not_selected :: file reports stale dependency pressure
- `src/copilot_probe_push_cycle_seq001_v001.py` kind=bug_chat attention=not_selected :: file reports stale dependency pressure
- `src/deepseek_daemon_seq001_v001.py` kind=bug_chat attention=not_selected :: file reports stale dependency pressure
- `src/file_email_plugin_seq001_v001.py` kind=bug_chat attention=not_selected :: file reports stale dependency pressure

### Local Write Queue

- `codex_compat.py` -> `MANIFEST.md`
- `logs/dead_stale_code_audit_latest.json` -> `MANIFEST.md`
- `logs/deepseek_code_completion_jobs.jsonl` -> `MANIFEST.md`
- `logs/deepseek_prompt_results.jsonl` -> `MANIFEST.md`
- `logs/edit_pairs.jsonl` -> `MANIFEST.md`
- `logs/file_self_sim_learning_latest.json` -> `MANIFEST.md`
- `logs/operator_intent_888.json` -> `MANIFEST.md`
- `logs/pigeon_compliance_push_latest.json` -> `MANIFEST.md`
- `src/batch_rewrite_sim_seq001_v001.py` -> `MANIFEST.md`
- `src/copilot_probe_push_cycle_seq001_v001.py` -> `MANIFEST.md`
- `src/deepseek_daemon_seq001_v001.py` -> `MANIFEST.md`
- `src/file_email_plugin_seq001_v001.py` -> `MANIFEST.md`
<!-- /manifest:folder-unified-state -->

<!-- manifest:master-persistent-state -->
## Master Persistent State

- state_doc: `MANIFEST.md`
- role: `opus_master_manifest_project_structure_and_persistent_state`
- folder_state_contract: `each folder writes one MANIFEST.md`
- latest_prompt_hash: `3d59c2fd6f5265a8`
- manifest_gate: `manifest_context_loaded`

### Project Structure

| Folder | Manifest | Changed In Scope |
|---|---|---:|
| `build/pigeon_legacy` | `build/pigeon_legacy/MANIFEST.md` | 2 |
| `build/pigeon_legacy/pigeon_brain/flow` | `build/pigeon_legacy/pigeon_brain/flow/MANIFEST.md` | 0 |
| `build/pigeon_legacy/pigeon_brain` | `build/pigeon_legacy/pigeon_brain/MANIFEST.md` | 0 |
| `build/pigeon_legacy/pigeon_compiler` | `build/pigeon_legacy/pigeon_compiler/MANIFEST.md` | 0 |
| `build/pigeon_legacy/scripts` | `build/pigeon_legacy/scripts/MANIFEST.md` | 0 |
| `build/pigeon_legacy/src` | `build/pigeon_legacy/src/MANIFEST.md` | 0 |
| `client` | `client/MANIFEST.md` | 0 |
| `logs` | `logs/MANIFEST.md` | 0 |
| `.` | `MANIFEST.md` | 57 |
| `pigeon_brain/flow/_resolve` | `pigeon_brain/flow/_resolve/MANIFEST.md` | 0 |
| `pigeon_brain/flow/backward_seq007` | `pigeon_brain/flow/backward_seq007/MANIFEST.md` | 0 |
| `pigeon_brain/flow/learning_loop_seq013` | `pigeon_brain/flow/learning_loop_seq013/MANIFEST.md` | 0 |
| `pigeon_brain/flow` | `pigeon_brain/flow/MANIFEST.md` | 0 |
| `pigeon_brain/flow/node_memory_seq008` | `pigeon_brain/flow/node_memory_seq008/MANIFEST.md` | 0 |
| `pigeon_brain/flow/prediction_scorer_seq014` | `pigeon_brain/flow/prediction_scorer_seq014/MANIFEST.md` | 0 |
| `pigeon_brain/flow/predictor_seq009` | `pigeon_brain/flow/predictor_seq009/MANIFEST.md` | 0 |
| `pigeon_brain/flow/分f_dvp_s010_v002_d0328_唤脉运观_λR` | `pigeon_brain/flow/分f_dvp_s010_v002_d0328_唤脉运观_λR/MANIFEST.md` | 0 |
| `pigeon_brain/flow/分f_dvp_s010_v003_d0328_唤脉运观_λR` | `pigeon_brain/flow/分f_dvp_s010_v003_d0328_唤脉运观_λR/MANIFEST.md` | 0 |
| `pigeon_brain/flow/分f_dvp_s010_v004_d0327_唤脉运观_λγ` | `pigeon_brain/flow/分f_dvp_s010_v004_d0327_唤脉运观_λγ/MANIFEST.md` | 0 |
| `pigeon_brain/flow/包p_cpk_s001_v002_d0324_缩分话_λε` | `pigeon_brain/flow/包p_cpk_s001_v002_d0324_缩分话_λε/MANIFEST.md` | 0 |
| `pigeon_brain/flow/唤w_noaw_s002_v003_d0401_脉运分话_λA` | `pigeon_brain/flow/唤w_noaw_s002_v003_d0401_脉运分话_λA/MANIFEST.md` | 0 |
| `pigeon_brain/flow/脉运w_vt_s006_v003_d0401_唤分话_λA` | `pigeon_brain/flow/脉运w_vt_s006_v003_d0401_唤分话_λA/MANIFEST.md` | 0 |
| `pigeon_brain/flow/虫f_bdm_s015_v001_d0410_λFT` | `pigeon_brain/flow/虫f_bdm_s015_v001_d0410_λFT/MANIFEST.md` | 0 |
| `pigeon_brain/flow/读f_fi_s016_v001_d0410_λFT` | `pigeon_brain/flow/读f_fi_s016_v001_d0410_λFT/MANIFEST.md` | 0 |
| `pigeon_brain` | `pigeon_brain/MANIFEST.md` | 0 |
| `pigeon_brain/仿f_dsm_s010_v002_d0323_缩分话_λP` | `pigeon_brain/仿f_dsm_s010_v002_d0323_缩分话_λP/MANIFEST.md` | 0 |
| `pigeon_brain/双f_dsb_s008_v002_d0323_缩分话_λP` | `pigeon_brain/双f_dsb_s008_v002_d0323_缩分话_λP/MANIFEST.md` | 0 |
| `pigeon_brain/型p_mo_s001_v002_d0323_读唤任_λP` | `pigeon_brain/型p_mo_s001_v002_d0323_读唤任_λP/MANIFEST.md` | 0 |
| `pigeon_brain/描p_ghm_s004_v002_d0323_缩环检意_λP` | `pigeon_brain/描p_ghm_s004_v002_d0323_缩环检意_λP/MANIFEST.md` | 0 |
| `pigeon_brain/环检p_ld_s005_v002_d0323_缩描意_λP` | `pigeon_brain/环检p_ld_s005_v002_d0323_缩描意_λP/MANIFEST.md` | 0 |
| `pigeon_brain/缩p_fdt_s006_v002_d0323_描环检意_λP` | `pigeon_brain/缩p_fdt_s006_v002_d0323_描环检意_λP/MANIFEST.md` | 0 |
| `pigeon_brain/观f_os_s007_v003_d0401_读谱建册_λA` | `pigeon_brain/观f_os_s007_v003_d0401_读谱建册_λA/MANIFEST.md` | 0 |
| `pigeon_brain/跑f_tr_s013_v002_d0323_缩分话_λP` | `pigeon_brain/跑f_tr_s013_v002_d0323_缩分话_λP/MANIFEST.md` | 0 |
| `pigeon_brain/钩w_th_s011_v002_d0323_缩分话_λP` | `pigeon_brain/钩w_th_s011_v002_d0323_缩分话_λP/MANIFEST.md` | 0 |
| `pigeon_compiler/cut_executor` | `pigeon_compiler/cut_executor/MANIFEST.md` | 0 |
| `pigeon_compiler/cut_executor/织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7` | `pigeon_compiler/cut_executor/织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7/MANIFEST.md` | 0 |
| `pigeon_compiler/docs` | `pigeon_compiler/docs/MANIFEST.md` | 0 |
| `pigeon_compiler/integrations` | `pigeon_compiler/integrations/MANIFEST.md` | 0 |
| `pigeon_compiler` | `pigeon_compiler/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/compliance_seq008` | `pigeon_compiler/rename_engine/compliance_seq008/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/f_he_s009_v005_d0401_改名册追跑_λA` | `pigeon_compiler/rename_engine/f_he_s009_v005_d0401_改名册追跑_λA/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/heal_seq009` | `pigeon_compiler/rename_engine/heal_seq009/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine` | `pigeon_compiler/rename_engine/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/manifest_builder_seq007` | `pigeon_compiler/rename_engine/manifest_builder_seq007/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/nametag_seq011` | `pigeon_compiler/rename_engine/nametag_seq011/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/registry_seq012` | `pigeon_compiler/rename_engine/registry_seq012/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR` | `pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc` | `pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX` | `pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/谱建f_mb_s007_v003_d0314_观重箱重拆_λD` | `pigeon_compiler/rename_engine/谱建f_mb_s007_v003_d0314_观重箱重拆_λD/MANIFEST.md` | 0 |
| `pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc` | `pigeon_compiler/rename_engine/追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc/MANIFEST.md` | 0 |
| `pigeon_compiler/runners/compiler_output/press_release_gen` | `pigeon_compiler/runners/compiler_output/press_release_gen/MANIFEST.md` | 0 |
| `pigeon_compiler/runners` | `pigeon_compiler/runners/MANIFEST.md` | 0 |
| `pigeon_compiler/runners/run_batch_compile_seq015` | `pigeon_compiler/runners/run_batch_compile_seq015/MANIFEST.md` | 0 |
| `pigeon_compiler/runners/净拆f_rcs_s010_v006_d0322_译测编深划_λW` | `pigeon_compiler/runners/净拆f_rcs_s010_v006_d0322_译测编深划_λW/MANIFEST.md` | 0 |
| `pigeon_compiler/runners/批编f_rbc_s015_v002_d0328_织谱建验_λR` | `pigeon_compiler/runners/批编f_rbc_s015_v002_d0328_织谱建验_λR/MANIFEST.md` | 0 |
| `pigeon_compiler/state_extractor` | `pigeon_compiler/state_extractor/MANIFEST.md` | 0 |
| `pigeon_compiler/weakness_planner` | `pigeon_compiler/weakness_planner/MANIFEST.md` | 0 |
| `scripts` | `scripts/MANIFEST.md` | 0 |
| `src/.operator_stats_seq008_v010_d0331__persi` | `src/.operator_stats_seq008_v010_d0331__persi/MANIFEST.md` | 0 |
| `src/codebase_detector` | `src/codebase_detector/MANIFEST.md` | 0 |
| `src/codebase_transmuter` | `src/codebase_transmuter/MANIFEST.md` | 0 |
| `src/cognitive/drift` | `src/cognitive/drift/MANIFEST.md` | 0 |
| `src/cognitive/drift/u_dbcc_s005_v001` | `src/cognitive/drift/u_dbcc_s005_v001/MANIFEST.md` | 0 |
| `src/cognitive/drift_seq003` | `src/cognitive/drift_seq003/MANIFEST.md` | 0 |
| `src/cognitive` | `src/cognitive/MANIFEST.md` | 0 |
| `src/cognitive/unsaid` | `src/cognitive/unsaid/MANIFEST.md` | 0 |
| `src/cognitive/unsaid/u_uo_s008_v001` | `src/cognitive/unsaid/u_uo_s008_v001/MANIFEST.md` | 0 |
| `src/cognitive/unsaid_seq002` | `src/cognitive/unsaid_seq002/MANIFEST.md` | 0 |
| `src/cognitive/隐p_un_s002_v002_d0315_缩分话_λν` | `src/cognitive/隐p_un_s002_v002_d0315_缩分话_λν/MANIFEST.md` | 0 |
| `src/context_compressor` | `src/context_compressor/MANIFEST.md` | 0 |
| `src/engagement_hooks` | `src/engagement_hooks/MANIFEST.md` | 0 |
| `src/escalation_engine/escalation_engine_data_loaders_seq003_v001` | `src/escalation_engine/escalation_engine_data_loaders_seq003_v001/MANIFEST.md` | 0 |
| `src/escalation_engine/escalation_engine_warnings_decomposed_seq014_v001` | `src/escalation_engine/escalation_engine_warnings_decomposed_seq014_v001/MANIFEST.md` | 0 |
| `src/escalation_engine` | `src/escalation_engine/MANIFEST.md` | 0 |
| `src` | `src/MANIFEST.md` | 0 |
| `src/module_identity` | `src/module_identity/MANIFEST.md` | 0 |
| `src/module_identity/module_identity_code_seq007_v001` | `src/module_identity/module_identity_code_seq007_v001/MANIFEST.md` | 0 |
| `src/numeric_surface` | `src/numeric_surface/MANIFEST.md` | 0 |
| `src/operator_stats` | `src/operator_stats/MANIFEST.md` | 0 |

### Master Intent Keys

- `pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX:route:thought_completer:minor`
- `build/pigeon_legacy/pigeon_brain/flow:route:raw_operator_prompt_fallback:minor`
- `build/pigeon_legacy/src:patch:promote_bug_notes_quick:minor`
- `pigeon_compiler/integrations:route:generated_opus_executor_prompt:minor`
- `root:route:they_are_not_ignored:minor`

### Surfaced Bug Queue

- `P1` `logs/deepseek_prompt_results.jsonl` stale pipeline lane: deepseek_results :: verify queued DeepSeek jobs have receipts or mark them expired
- `P1` `logs/deepseek_code_completion_jobs.jsonl` stale pipeline lane: code_completion_jobs :: close stale code job queue before creating more file jobs
- `P2` `logs/file_self_sim_learning_latest.json` stale pipeline lane: file_self_learning :: rerun file self-learning so manifests reflect recent prompt behavior
- `P2` `logs/edit_pairs.jsonl` stale pipeline lane: edit_pairs :: regenerate prompt-to-edit pairs from git and prompt journal
- `P1` `logs/operator_intent_888.json` weak cognitive probe coverage :: rebuild operator intent labels from prompt journal before trusting behavioral routing
- `P2` `codex_compat.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `src/file_email_plugin_seq001_v001.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `src/deepseek_daemon_seq001_v001.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `src/batch_rewrite_sim_seq001_v001.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `src/copilot_probe_push_cycle_seq001_v001.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `src/file_self_sim_learning_seq001_v001.py` file reports stale dependency pressure :: route file opinion into folder manifest and master bug queue
- `P2` `logs/pigeon_compliance_push_latest.json` compiler saw compliance warning pressure :: sample warning owners and schedule bounded split/cleanup jobs

### File Bug Chat

- `logs/deepseek_prompt_results.jsonl` I keep getting touched because stale pipeline lane: deepseek_results. I am in this sim because I help closing DeepSeek job/result receipts. My evidence is age=3186.0m max=90m entries=37. My proposed fix is: verify queued DeepSeek jobs have receipts or mark them expired.
- `logs/deepseek_code_completion_jobs.jsonl` I keep getting touched because stale pipeline lane: code_completion_jobs. I am in this sim because I help closing DeepSeek job/result receipts. My evidence is age=10251.1m max=180m entries=61. My proposed fix is: close stale code job queue before creating more file jobs.
- `logs/file_self_sim_learning_latest.json` I keep getting touched because stale pipeline lane: file_self_learning. I am in this sim because I help making file pressure visible to the master manifest. My evidence is age=2640.4m max=90m entries=1. My proposed fix is: rerun file self-learning so manifests reflect recent prompt behavior.
- `logs/edit_pairs.jsonl` I keep getting touched because stale pipeline lane: edit_pairs. I am in this sim because I help teaching prompts which edits actually happened. My evidence is age=5313.1m max=720m entries=79. My proposed fix is: regenerate prompt-to-edit pairs from git and prompt journal.
- `logs/operator_intent_888.json` I keep getting touched because weak cognitive probe coverage. I am in this sim because I help keeping operator intent labels usable. My evidence is unknown_ratio=0.579 coverage_gap=470. My proposed fix is: rebuild operator intent labels from prompt journal before trusting behavioral routing.
- `codex_compat.py` I keep getting touched because file reports stale dependency pressure. I am in this sim because I help making file pressure visible to the master manifest. My evidence is I was stamping unknown cognition too often; prompt-text inference should now keep Codex probing from going blind. deps=deepseek_results, code_completion_jobs, file_self_learning, edit_pairs. My proposed fix is: route file opinion into folder manifest and master bug queue.

### Root Sim Key File

- `ROOT_SIM_KEYS.md` :: called=53

### Opus Micro-Pulse Runtime

- `logs/opus_micro_pulse_latest.json` :: class=debug executor=codex_execution_session predicted=16

### Cannon Execution Gate

- `logs/cannon_execution_gate_latest.json` :: status=cleared payload_ready=true predicted=16

### Persistent State Files

- `logs/prompt_context_packet_latest.json` :: exists=true
- `logs/copilot_prompt_box_latest.md` :: exists=true
- `logs/intent_graph_latest.json` :: exists=true
- `logs/operator_syntax_triggers.json` :: exists=true
- `logs/opus_master_manifest_session.json` :: exists=true
- `logs/deepseek_push_audit_latest.json` :: exists=true
- `logs/file_bug_surface_latest.json` :: exists=true
- `logs/file_bug_chat_latest.json` :: exists=true
- `logs/root_sim_key_file_latest.json` :: exists=true
- `logs/opus_micro_pulse_latest.json` :: exists=true
- `logs/opus_executor_prompt_latest.md` :: exists=true
- `logs/prompt_cannon_job_latest.json` :: exists=true
- `logs/cannon_execution_gate_latest.json` :: exists=true
- `logs/backward_file_intelligence_learning_pending_latest.json` :: exists=true
<!-- /manifest:master-persistent-state -->
