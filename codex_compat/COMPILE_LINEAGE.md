# Compile Lineage - codex_compat.py

- schema: `pigeon_compile_lineage/v1`
- compiled_at: `2026-06-05T23:48:51.951268+00:00`
- target_dir: `codex_compat`
- file_count: `44`

| Source Symbols | Generated File | Identity |
|---|---|---|
| `_utc_now, _words, _parse_deleted_words, _state_from_deletions, _append_jsonl` | `codex_compat/codex_compat_seq001_v001.py` | `codex_compat.py::_utc_now|_words|_parse_deleted_words|_state_from_deletions|_append_jsonl` |
| `_write_text_resilient, _load_jsonl_tail, _repo_root, _ensure_repo_on_path` | `codex_compat/codex_compat_seq002_v001.py` | `codex_compat.py::_write_text_resilient|_load_jsonl_tail|_repo_root|_ensure_repo_on_path` |
| `_load_entropy_module, _git_status` | `codex_compat/codex_compat_seq003_v001.py` | `codex_compat.py::_load_entropy_module|_git_status` |
| `_refresh_entropy, _load_intent_reconstructor` | `codex_compat/codex_compat_seq004_v001.py` | `codex_compat.py::_refresh_entropy|_load_intent_reconstructor` |
| `_load_context_select_agent, _load_intent_numeric` | `codex_compat/codex_compat_seq005_v001.py` | `codex_compat.py::_load_context_select_agent|_load_intent_numeric` |
| `train_numeric_surface, predict_numeric_files` | `codex_compat/codex_compat_seq006_v001.py` | `codex_compat.py::train_numeric_surface|predict_numeric_files` |
| `_run_sim_buffer, _latest_json, _replace_managed_block` | `codex_compat/codex_compat_seq007_v001.py` | `codex_compat.py::_run_sim_buffer|_latest_json|_replace_managed_block` |
| `_render_pre_prompt_block` | `codex_compat/codex_compat_seq008_v001.py` | `codex_compat.py::_render_pre_prompt_block` |
| `_inject_pre_prompt_state, _inject_dynamic_context_pack` | `codex_compat/codex_compat_seq009_v001.py` | `codex_compat.py::_inject_pre_prompt_state|_inject_dynamic_context_pack` |
| `_running_prompt_summary, _task_queue_summary` | `codex_compat/codex_compat_seq010_v001.py` | `codex_compat.py::_running_prompt_summary|_task_queue_summary` |
| `_build_live_prompt_telemetry` | `codex_compat/codex_compat_seq011_v001.py` | `codex_compat.py::_build_live_prompt_telemetry` |
| `_render_prompt_telemetry_block, _write_live_prompt_telemetry` | `codex_compat/codex_compat_seq012_v001.py` | `codex_compat.py::_render_prompt_telemetry_block|_write_live_prompt_telemetry` |
| `_render_current_query_block` | `codex_compat/codex_compat_seq013_v001.py` | `codex_compat.py::_render_current_query_block` |
| `_render_staleness_alert_block, _write_copilot_live_query_blocks` | `codex_compat/codex_compat_seq014_v001.py` | `codex_compat.py::_render_staleness_alert_block|_write_copilot_live_query_blocks` |
| `_surface_activity` | `codex_compat/codex_compat_seq015_v001.py` | `codex_compat.py::_surface_activity` |
| `_log_counts, _git_focus_files, _deepseek_default_model` | `codex_compat/codex_compat_seq016_v001.py` | `codex_compat.py::_log_counts|_git_focus_files|_deepseek_default_model` |
| `_deepseek_api_key_present, launch_deepseek_daemon` | `codex_compat/codex_compat_seq017_v001.py` | `codex_compat.py::_deepseek_api_key_present|launch_deepseek_daemon` |
| `enqueue_deepseek_prompt_job` | `codex_compat/codex_compat_seq018_v001.py` | `codex_compat.py::enqueue_deepseek_prompt_job` |
| `_build_focus_files` | `codex_compat/codex_compat_seq019_v001.py` | `codex_compat.py::_build_focus_files` |
| `_build_opus_instruction_layer` | `codex_compat/codex_compat_seq020_v001.py` | `codex_compat.py::_build_opus_instruction_layer` |
| `_add_file_sim_focus_files` | `codex_compat/codex_compat_seq021_v001.py` | `codex_compat.py::_add_file_sim_focus_files` |
| `build_dynamic_context_pack` | `codex_compat/codex_compat_seq022_v001.py` | `codex_compat.py::build_dynamic_context_pack` |
| `_render_dynamic_context_pack` | `codex_compat/codex_compat_seq023_v001.py` | `codex_compat.py::_render_dynamic_context_pack` |
| `_fire_file_sim` | `codex_compat/codex_compat_seq024_v001.py` | `codex_compat.py::_fire_file_sim` |
| `_record_intent_loop, _emit_codex_prompt_email, _bind_intent_loop_response` | `codex_compat/codex_compat_seq025_v001.py` | `codex_compat.py::_record_intent_loop|_emit_codex_prompt_email|_bind_intent_loop_response` |
| `_bind_intent_loop_edit, close_intent_loop, get_intent_loop_status, _parse_iso_ts, _latest_log_ts` | `codex_compat/codex_compat_seq026_v001.py` | `codex_compat.py::_bind_intent_loop_edit|close_intent_loop|get_intent_loop_status|_parse_iso_ts|_latest_log_ts` |
| `audit_stale_dates` | `codex_compat/codex_compat_seq027_v001.py` | `codex_compat.py::audit_stale_dates` |
| `run_pre_prompt_from_composition` | `codex_compat/codex_compat_seq028_v001.py` | `codex_compat.py::run_pre_prompt_from_composition` |
| `run_pre_prompt_pipeline` | `codex_compat/codex_compat_seq029_v001.py` | `codex_compat.py::run_pre_prompt_pipeline` |
| `select_context` | `codex_compat/codex_compat_seq030_v001.py` | `codex_compat.py::select_context` |
| `refresh_state` | `codex_compat/codex_compat_seq031_v001.py` | `codex_compat.py::refresh_state` |
| `_render_state_markdown` | `codex_compat/codex_compat_seq032_v001.py` | `codex_compat.py::_render_state_markdown` |
| `_load_json, _next_session_n, _classify_intent` | `codex_compat/codex_compat_seq033_v001.py` | `codex_compat.py::_load_json|_next_session_n|_classify_intent` |
| `log_prompt` | `codex_compat/codex_compat_seq034_v001.py` | `codex_compat.py::log_prompt` |
| `log_composition` | `codex_compat/codex_compat_seq035_v001.py` | `codex_compat.py::log_composition` |
| `_build_unsaid_reconstruction, _write_unsaid` | `codex_compat/codex_compat_seq036_v001.py` | `codex_compat.py::_build_unsaid_reconstruction|_write_unsaid` |
| `log_response` | `codex_compat/codex_compat_seq037_v001.py` | `codex_compat.py::log_response` |
| `_git_changed_files` | `codex_compat/codex_compat_seq038_v001.py` | `codex_compat.py::_git_changed_files` |
| `log_edit` | `codex_compat/codex_compat_seq039_v001.py` | `codex_compat.py::log_edit` |
| `capture_pair, record_entropy_shed` | `codex_compat/codex_compat_seq040_v001.py` | `codex_compat.py::capture_pair|record_entropy_shed` |
| `push_intent_resolver, _text_from_event` | `codex_compat/codex_compat_seq041_v001.py` | `codex_compat.py::push_intent_resolver|_text_from_event` |
| `import_jsonl` | `codex_compat/codex_compat_seq042_v001.py` | `codex_compat.py::import_jsonl` |
| `build_parser` | `codex_compat/codex_compat_seq043_v001.py` | `codex_compat.py::build_parser` |
| `main` | `codex_compat/codex_compat_seq044_v001.py` | `codex_compat.py::main` |
