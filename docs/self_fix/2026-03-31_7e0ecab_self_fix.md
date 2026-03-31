# Self-Fix Report — 2026-03-31 7e0ecab

Scanned 259 modules, 246 in import graph.

## Problems Found: 23

### 1. [HIGH] over_hard_cap
- **File**: pigeon_brain/live_server_seq012_v003_d0324__websocket_server_for_live_execution_lc_8888_word_backpropagation.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 2. [HIGH] over_hard_cap
- **File**: pigeon_brain/live_server_seq012_v004_d0324__websocket_server_for_live_execution_lc_8888_word_backpropagation.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 3. [HIGH] over_hard_cap
- **File**: pigeon_brain/live_server_seq012_v004_d0324__websocket_server_for_live_execution_lc_per_prompt_deleted.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 4. [HIGH] over_hard_cap
- **File**: pigeon_compiler/runners/run_batch_compile_seq015_v002_d0328__compile_entire_codebase_to_pigeon_lc_dynamic_import_resolvers.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 5. [HIGH] over_hard_cap
- **File**: src/push_narrative_seq012_v006_d0327__generate_per_push_narrative_each_lc_push_narratives_timeout.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 6. [HIGH] over_hard_cap
- **File**: src/research_lab_seq029_v002_d0330__the_system_studying_the_system_lc_research_lab_autonomous.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 7. [HIGH] over_hard_cap
- **File**: src/shard_manager_seq026_v002_d0330__local_memory_shard_manager_markdown_lc_gemini_flash_enricher.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 8. [HIGH] over_hard_cap
- **File**: src/training_pairs_seq027_v002_d0330__training_pair_generator_for_the_lc_gemini_flash_enricher.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 9. [HIGH] over_hard_cap
- **File**: src/training_writer_seq028_v002_d0330__end_of_prompt_training_pair_lc_gemini_flash_enricher.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 10. [HIGH] over_hard_cap
- **File**: src/unified_signal_seq026_v002_d0330__joins_all_telemetry_into_canonical_lc_gemini_flash_enricher.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 11. [HIGH] over_hard_cap
- **File**: src/voice_style_seq028_v002_d0330__voice_style_personality_adapter_lc_gemini_flash_enricher.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 12. [HIGH] over_hard_cap
- **File**: src/.operator_stats_seq008_v008_d0331__persistent_markdown_memory_file_lc_intent_deletion_pipeline.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 13. [HIGH] over_hard_cap
- **File**: src/.operator_stats_seq008_v010_d0331__persistent_markdown_memory_file_lc_intent_deletion_pipeline.py
- **Fix**: Auto-compile with pigeon compiler (run_clean_split)

### 14. [LOW] dead_export
- **File**: src/context_budget_seq004_v008_d0321__context_budget_scorer_for_llm_lc_fire_full_post.py
- **Line**: 37
- **Function**: `default_budget_config()`
- **Fix**: Consider removing or wiring default_budget_config() into pipeline

### 15. [LOW] dead_export
- **File**: src/file_heat_map_seq011_v004_d0317__tracks_cognitive_load_per_module_lc_pulse_telemetry_prompt.py
- **Line**: 34
- **Function**: `update_heat_map()`
- **Fix**: Consider removing or wiring update_heat_map() into pipeline

### 16. [LOW] dead_export
- **File**: src/file_heat_map_seq011_v004_d0317__tracks_cognitive_load_per_module_lc_pulse_telemetry_prompt.py
- **Line**: 128
- **Function**: `load_registry_churn()`
- **Fix**: Consider removing or wiring load_registry_churn() into pipeline

### 17. [LOW] dead_export
- **File**: src/rework_detector_seq009_v005_d0321__measures_ai_answer_quality_from_lc_implement_all_18.py
- **Line**: 126
- **Function**: `load_rework_stats()`
- **Fix**: Consider removing or wiring load_rework_stats() into pipeline

### 18. [LOW] dead_export
- **File**: src/shard_manager_seq026_v002_d0330__local_memory_shard_manager_markdown_lc_gemini_flash_enricher.py
- **Line**: 274
- **Function**: `resolve_contradiction()`
- **Fix**: Consider removing or wiring resolve_contradiction() into pipeline

### 19. [LOW] dead_export
- **File**: src/shard_manager_seq026_v002_d0330__local_memory_shard_manager_markdown_lc_gemini_flash_enricher.py
- **Line**: 422
- **Function**: `learn_from_rework()`
- **Fix**: Consider removing or wiring learn_from_rework() into pipeline

### 20. [LOW] dead_export
- **File**: src/task_queue_seq018_v002_d0317__copilot_driven_task_tracking_linked_lc_task_queue_system.py
- **Line**: 66
- **Function**: `mark_in_progress()`
- **Fix**: Consider removing or wiring mark_in_progress() into pipeline

### 21. [LOW] dead_export
- **File**: src/training_writer_seq028_v002_d0330__end_of_prompt_training_pair_lc_gemini_flash_enricher.py
- **Line**: 215
- **Function**: `backfill_rework()`
- **Fix**: Consider removing or wiring backfill_rework() into pipeline

### 22. [INFO] high_coupling
- **File**: pigeon_compiler/rename_engine/compliance_seq008_v004_d0315__line_count_enforcer_split_recommender_lc_verify_pigeon_plugin.py
- **Fan-in**: 8 dependents
- **Fix**: Module has 8 dependents — changes here break many files

### 23. [INFO] high_coupling
- **File**: pigeon_compiler/integrations/deepseek_adapter_seq001_v006_d0322__deepseek_api_client_lc_stage_78_hook.py
- **Fan-in**: 5 dependents
- **Fix**: Module has 5 dependents — changes here break many files
