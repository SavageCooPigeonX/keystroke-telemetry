# Self-Fix Report — 2026-03-16 first_run

Scanned 86 modules, 73 in import graph.

## Problems Found: 18

### 1. [CRITICAL] hardcoded_import
- **File**: stress_test.py
- **Line**: 15
- **Import**: `src.logger_seq003_v002_d0315__core_keystroke_telemetry_logger_lc_verify_pigeon_plugin`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 2. [CRITICAL] hardcoded_import
- **File**: stress_test.py
- **Line**: 16
- **Import**: `src.resistance_bridge_seq006_v002_d0315__bridge_between_keystroke_telemetry_and_lc_verify_pigeon_plugin`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 3. [CRITICAL] hardcoded_import
- **File**: test_all.py
- **Line**: 13
- **Import**: `src.logger_seq003_v002_d0315__core_keystroke_telemetry_logger_lc_verify_pigeon_plugin`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 4. [CRITICAL] hardcoded_import
- **File**: test_all.py
- **Line**: 14
- **Import**: `src.context_budget_seq004_v005_d0316__context_budget_scorer_for_llm_lc_fire_full_coaching`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 5. [CRITICAL] hardcoded_import
- **File**: test_all.py
- **Line**: 15
- **Import**: `src.drift_watcher_seq005_v002_d0315__drift_detection_for_live_llm_lc_verify_pigeon_plugin`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 6. [CRITICAL] hardcoded_import
- **File**: test_all.py
- **Line**: 16
- **Import**: `src.resistance_bridge_seq006_v002_d0315__bridge_between_keystroke_telemetry_and_lc_verify_pigeon_plugin`
- **Fix**: Use glob-based dynamic import instead of hardcoded name

### 7. [HIGH] query_noise
- **Count**: 25
- **Fix**: Filter "(background)" queries in extension flush — use active filename instead

### 8. [LOW] dead_export
- **File**: src/context_budget_seq004_v005_d0316__context_budget_scorer_for_llm_lc_fire_full_coaching.py
- **Line**: 31
- **Function**: `default_budget_config()`
- **Fix**: Consider removing or wiring default_budget_config() into pipeline

### 9. [LOW] dead_export
- **File**: src/context_budget_seq004_v005_d0316__context_budget_scorer_for_llm_lc_fire_full_coaching.py
- **Line**: 120
- **Function**: `default_budget_config()`
- **Fix**: Consider removing or wiring default_budget_config() into pipeline

### 10. [LOW] dead_export
- **File**: src/file_heat_map_seq011_v003_d0316__tracks_cognitive_load_per_module_lc_fix_deep_signal.py
- **Line**: 29
- **Function**: `update_heat_map()`
- **Fix**: Consider removing or wiring update_heat_map() into pipeline

### 11. [LOW] dead_export
- **File**: src/file_heat_map_seq011_v003_d0316__tracks_cognitive_load_per_module_lc_fix_deep_signal.py
- **Line**: 89
- **Function**: `load_heat_map()`
- **Fix**: Consider removing or wiring load_heat_map() into pipeline

### 12. [LOW] dead_export
- **File**: src/file_heat_map_seq011_v003_d0316__tracks_cognitive_load_per_module_lc_fix_deep_signal.py
- **Line**: 123
- **Function**: `load_registry_churn()`
- **Fix**: Consider removing or wiring load_registry_churn() into pipeline

### 13. [LOW] dead_export
- **File**: src/query_memory_seq010_v002_d0316__recurring_query_detector_unsaid_thought_lc_add_deep_operator.py
- **Line**: 42
- **Function**: `record_query()`
- **Fix**: Consider removing or wiring record_query() into pipeline

### 14. [LOW] dead_export
- **File**: src/query_memory_seq010_v002_d0316__recurring_query_detector_unsaid_thought_lc_add_deep_operator.py
- **Line**: 84
- **Function**: `load_query_memory()`
- **Fix**: Consider removing or wiring load_query_memory() into pipeline

### 15. [LOW] dead_export
- **File**: src/rework_detector_seq009_v003_d0316__measures_ai_answer_quality_from_lc_fix_deep_signal.py
- **Line**: 27
- **Function**: `score_rework()`
- **Fix**: Consider removing or wiring score_rework() into pipeline

### 16. [LOW] dead_export
- **File**: src/rework_detector_seq009_v003_d0316__measures_ai_answer_quality_from_lc_fix_deep_signal.py
- **Line**: 61
- **Function**: `record_rework()`
- **Fix**: Consider removing or wiring record_rework() into pipeline

### 17. [LOW] dead_export
- **File**: src/rework_detector_seq009_v003_d0316__measures_ai_answer_quality_from_lc_fix_deep_signal.py
- **Line**: 80
- **Function**: `load_rework_stats()`
- **Fix**: Consider removing or wiring load_rework_stats() into pipeline

### 18. [INFO] high_coupling
- **File**: src/timestamp_utils_seq001_v002_d0315__millisecond_epoch_timestamp_utility_lc_verify_pigeon_plugin.py
- **Fan-in**: 6 dependents
- **Fix**: Module has 6 dependents — changes here break many files
