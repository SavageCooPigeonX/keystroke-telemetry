# Pigeon Compliance Reduction Roadmap

Status as of 2026-06-29:

- Full report: `py scripts/maintain_compliance.py --all --json`
- Current debt: 39 over-cap Python files out of 1866 checked.
- Risk split: 11 medium, 28 high.
- Push policy: branch-aware changed-file gate blocks new or worsened debt; strict full-tree blocking is opt-in with `PIGEON_FULL_COMPLIANCE_BLOCK=1`.

## Batch 1: Smallest Medium Files

Goal: reduce the easiest medium-risk files first and prove the branch-aware gate stays quiet.

1. `pigeon_compiler/git_plugin/git_plugin_seq021_v001.py` - 206 lines
2. `pigeon_compiler/compile_lineage.py` - 226 lines
3. `src/manifest_state_cycle_seq001_v001.py` - 228 lines
4. `src/file_interlinked_naming_sim_seq001_v001.py` - 245 lines
5. `src/file_sim_deepseek_lane_seq001_v001.py` - 263 lines

## Batch 2: Shared Medium Runtimes

Goal: split by responsibility while preserving import facades and focused tests.

1. `src/operator_response_policy_seq001_v002_d0510__operator_response_policy_for_codex_lc_feat_bind_keystroke_telemetry.py` - 326 lines
2. `src/opus_orchestrator_runtime_seq001_v001.py` - 331 lines
3. `src/registry_identity_bridge_seq001_v002_d0605__seq_pairing_aliases_md_anchors_lc_patch_registry.py` - 427 lines
4. `src/hush_intent_runtime_seq001_v001.py` - 450 lines
5. `src/folder_context_coupling_seq001_v001.py` - 455 lines
6. Self-fix Unicode-named module matching `src/*sf_s013*v012*d0402*VR*oc.py` - 761 lines

## Batch 3: High-Risk Small Files

Goal: files just over the cap, with careful facade/import tests.

- `src/session_macro_cycle_support_seq001_v001.py` - 204 lines
- `src/operator_syntax_triggers_seq001_v001.py` - 207 lines
- `src/file_bug_surface_seq001_v001.py` - 207 lines
- `pigeon_compiler/bones/nl_parsers_seq001_v003_d0314__extracted_from_hush_nl_detection_lc_desc_upgrade.py` - 208 lines
- `src/thought_completer.py` - 209 lines
- `src/unified_manifest_state_seq001_v001.py` - 211 lines
- `src/root_sim_key_file_seq001_v001.py` - 218 lines
- `tests/regression/test_tc_intent_keys.py` - 267 lines
- `src/intent_identity_naming_seq001_v002_d0605__itid_lh_eci_replaces_meaningless_lc_replace_seq_with.py` - 280 lines
- `src/tc_semantic_profile_seq001_v001.py` - 285 lines

## Batch 4: Entry Points And Compiler Surfaces

Goal: extract helpers, keep command/facade behavior stable, and test through public entrypoints.

- Unicode-named Pigeon runner matching `pigeon_compiler/runners/*rpl_s009*v004*.py` - 262 lines
- Unicode-named clean-split runner matching `pigeon_compiler/runners/*rcs_s010*v007*d0510*TL*oc.py` - 354 lines
- `pigeon_compiler/organization_pass_seq001_v001.py` - 354 lines
- `src/tc_onboard_seq001_v001.py` - 368 lines
- `src/file_interview_mode_seq001_v001.py` - 383 lines
- `pigeon_compiler/bones/pq_search_utils_seq001_v003_d0314__extracted_from_hush_pre_query_lc_desc_upgrade.py` - 394 lines
- `src/tc_file_encoder_seq001_v001.py` - 441 lines
- `src/tc_prompt_composer_seq001_v001.py` - 523 lines
- `src/opus_prompt_box_seq001_v001.py` - 533 lines
- `src/intent_outcome_binder_seq001_v002_d0510__closes_the_intent_outcome_loop_lc_feat_bind_keystroke_telemetry.py` - 592 lines
- `pigeon_compiler/git_plugin/git_plugin_seq020_v001.py` - 638 lines
- `src/opus_micro_pulse_runtime_seq001_v001.py` - 871 lines
- `scripts/analyze_prompt_behavior.py` - 1045 lines

## Batch 5: Last-Mile Facades

Goal: leave the largest and most imported files for manual facade work after the smaller queue proves the pattern.

- `src/batch_rewrite_sim_seq001_v002_d0510__proposal_only_batch_rewrite_simulator_lc_feat_bind_keystroke_telemetry.py` - 1646 lines
- `pigeon_compiler/git_plugin.py` - 1669 lines
- `src/file_self_sim_learning_seq001_v001.py` - 1914 lines
- `src/file_email_plugin_seq001_v001.py` - 2413 lines
- `codex_compat.py` - 2772 lines

## Done Criteria

- `py scripts/pigeon_changed_file_gate_seq001_v001__block_new_overcap_lc_push_compliance.py` reports zero changed-file violations.
- Focused import/facade tests pass for each touched module.
- The full compliance report decreases monotonically or the branch explains why a touched legacy file stayed over-cap.
- No generated manifest or local operator data is staged.
