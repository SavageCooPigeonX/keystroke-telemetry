# codex_compat/ MANIFEST.md
## Pigeon-Extracted from `codex_compat.py`

**Strategy**: one function per file, group tiny helpers, init_exports only public names
**Date**: 2026-05-09

---

## 📁 FILES

| File | Lines | Status |
|------|-------|--------|
| `codex_compat_utc_now_seq001_v001.py` | 7 | OK |
| `codex_compat_words_seq002_v001.py` | 6 | OK |
| `codex_compat_parse_deleted_words_seq003_v001.py` | 24 | OK |
| `codex_compat_state_from_deletions_seq004_v001.py` | 12 | OK |
| `codex_compat_append_jsonl_seq005_v001.py` | 11 | OK |
| `codex_compat_write_text_resilient_seq006_v001.py` | 20 | OK |
| `codex_compat_load_jsonl_tail_seq007_v001.py` | 21 | OK |
| `codex_compat_repo_root_seq008_v001.py` | 10 | OK |
| `codex_compat_ensure_repo_on_path_seq009_v001.py` | 10 | OK |
| `codex_compat_load_entropy_module_seq010_v001.py` | 17 | OK |
| `codex_compat_git_status_seq011_v001.py` | 22 | OK |
| `codex_compat_refresh_entropy_seq012_v001.py` | 31 | OK |
| `codex_compat_load_intent_reconstructor_seq013_v001.py` | 17 | OK |
| `codex_compat_load_context_select_agent_seq014_v001.py` | 19 | OK |
| `codex_compat_load_intent_numeric_seq015_v001.py` | 33 | OK |
| `codex_compat_train_numeric_surface_seq016_v001.py` | 28 | OK |
| `codex_compat_predict_numeric_files_seq017_v001.py` | 27 | OK |
| `codex_compat_run_sim_buffer_seq018_v001.py` | 43 | OK |
| `codex_compat_latest_json_seq019_v001.py` | 11 | OK |
| `codex_compat_replace_managed_block_seq020_v001.py` | 9 | OK |
| `codex_compat_render_pre_prompt_block_seq021_v001.py` | 63 | WARN (63) |
| `codex_compat_inject_pre_prompt_state_seq022_v001.py` | 24 | OK |
| `codex_compat_inject_dynamic_context_pack_seq023_v001.py` | 24 | OK |
| `codex_compat_running_prompt_summary_seq024_v001.py` | 36 | OK |
| `codex_compat_task_queue_summary_seq025_v001.py` | 19 | OK |
| `codex_compat_build_live_prompt_telemetry_seq026_v001.py` | 70 | WARN (70) |
| `codex_compat_render_prompt_telemetry_block_seq027_v001.py` | 21 | OK |
| `codex_compat_write_live_prompt_telemetry_seq028_v001.py` | 31 | OK |
| `codex_compat_render_current_query_block_seq029_v001.py` | 37 | OK |
| `codex_compat_render_staleness_alert_block_seq030_v001.py` | 25 | OK |
| `codex_compat_write_copilot_live_query_blocks_seq031_v001.py` | 29 | OK |
| `codex_compat_surface_activity_seq032_v001.py` | 40 | OK |
| `codex_compat_log_counts_seq033_v001.py` | 39 | OK |
| `codex_compat_git_focus_files_seq034_v001.py` | 14 | OK |
| `codex_compat_deepseek_default_model_seq035_v001.py` | 7 | OK |
| `codex_compat_deepseek_api_key_present_seq036_v001.py` | 19 | OK |
| `codex_compat_launch_deepseek_daemon_seq037_v001.py` | 35 | OK |
| `codex_compat_enqueue_deepseek_prompt_job_seq038_v001.py` | 69 | WARN (69) |
| `codex_compat_build_focus_files_seq039_v001.py` | 75 | WARN (75) |
| `codex_compat_build_opus_instruction_layer_seq040_v001.py` | 58 | WARN (58) |
| `codex_compat_add_file_sim_focus_files_seq041_v001.py` | 31 | OK |
| `codex_compat_build_dynamic_context_pack_seq042_v001.py` | 162 | WARN (162) |
| `codex_compat_render_dynamic_context_pack_seq043_v001.py` | 199 | WARN (199) |
| `codex_compat_fire_file_sim_seq044_v001.py` | 49 | OK |
| `codex_compat_record_intent_loop_seq045_v001.py` | 31 | OK |
| `codex_compat_emit_codex_prompt_email_seq046_v001.py` | 18 | OK |
| `codex_compat_bind_intent_loop_response_seq047_v001.py` | 15 | OK |
| `codex_compat_bind_intent_loop_edit_seq048_v001.py` | 15 | OK |
| `codex_compat_close_intent_loop_seq049_v001.py` | 20 | OK |
| `codex_compat_get_intent_loop_status_seq050_v001.py` | 15 | OK |
| `codex_compat_parse_iso_ts_seq051_v001.py` | 16 | OK |
| `codex_compat_latest_log_ts_seq052_v001.py` | 18 | OK |
| `codex_compat_audit_stale_dates_seq053_v001.py` | 90 | WARN (90) |
| `codex_compat_run_pre_prompt_from_composition_seq054_v001.py` | 123 | WARN (123) |
| `codex_compat_run_pre_prompt_pipeline_seq055_v001.py` | 159 | WARN (159) |
| `codex_compat_select_context_seq056_v001.py` | 58 | WARN (58) |
| `codex_compat_refresh_state_seq057_v001.py` | 66 | WARN (66) |
| `codex_compat_render_state_markdown_seq058_v001.py` | 151 | WARN (151) |
| `codex_compat_load_json_seq059_v001.py` | 15 | OK |
| `codex_compat_next_session_n_seq060_v001.py` | 15 | OK |
| `codex_compat_classify_intent_seq061_v001.py` | 26 | OK |
| `codex_compat_log_prompt_seq062_v001.py` | 122 | WARN (122) |
| `codex_compat_log_composition_seq063_v001.py` | 62 | WARN (62) |
| `codex_compat_build_unsaid_reconstruction_seq064_v001.py` | 8 | OK |
| `codex_compat_write_unsaid_seq065_v001.py` | 39 | OK |
| `codex_compat_log_response_seq066_v001.py` | 81 | WARN (81) |
| `codex_compat_git_changed_files_seq067_v001.py` | 20 | OK |
| `codex_compat_log_edit_seq068_v001.py` | 60 | WARN (60) |
| `codex_compat_capture_pair_seq069_v001.py` | 28 | OK |
| `codex_compat_record_entropy_shed_seq070_v001.py` | 22 | OK |
| `codex_compat_push_intent_resolver_seq071_v001.py` | 25 | OK |
| `codex_compat_text_from_event_seq072_v001.py` | 19 | OK |
| `codex_compat_import_jsonl_seq073_v001.py` | 62 | WARN (62) |
| `codex_compat_build_parser_seq074_v001.py` | 106 | WARN (106) |
| `codex_compat_main_seq075_v001.py` | 139 | WARN (139) |

---

## 🔌 EXPORTS

- `_render_dynamic_context_pack()`
- `train_numeric_surface()`
- `predict_numeric_files()`
- `launch_deepseek_daemon()`
- `enqueue_deepseek_prompt_job()`
- `build_dynamic_context_pack()`
- `close_intent_loop()`
- `get_intent_loop_status()`
- `audit_stale_dates()`
- `run_pre_prompt_from_composition()`
- `run_pre_prompt_pipeline()`
- `select_context()`
- `refresh_state()`
- `log_prompt()`
- `log_composition()`
- `log_response()`
- `log_edit()`
- `capture_pair()`
- `record_entropy_shed()`
- `push_intent_resolver()`
- `import_jsonl()`
- `build_parser()`
- `main()`

---

## 📦 PROMPT BOX — CODEX_COMPAT TASKS
*Generated by Pigeon Compiler | 2026-05-09*

- [ ] **CODEX_COMPAT-001**: Verify all imports resolve correctly
- [ ] **CODEX_COMPAT-002**: Run folder_auditor on this folder
- [ ] **CODEX_COMPAT-003**: Add unit tests for extracted functions
