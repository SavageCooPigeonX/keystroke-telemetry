# u_pj_s019_v003_d0404_λNU_βoc/ MANIFEST.md
## Pigeon-Extracted from `u_pj_s019_v003_d0404_λNU_βoc.py`
**Version**: v1.0.0 | **Last Updated**: 2026-04-13

---

## FILES

| File | Lines | Functions |
|------|-------|-----------|
| `__init__.py` | 3 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_append_journal_seq025_v001.py` | 10 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_build_snapshot_decomposed_seq015_v001.py` | 65 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_candidate_comps_seq009_v001.py` | 32 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_coaching_seq016_v001.py` | 21 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_composition_key_seq004_v001.py` | 14 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_constants_seq001_v001.py` | 55 🟡 | JOURNAL_PATH, SNAPSHOT_PATH, COMPS_PATH, PROMPT_COMPS_PATH, HEAT_PATH, TASK_PATH, PROFILE_PATH, EDIT_PAIRS, MUTATIONS_PATH, COPILOT_PATH, MAX_COMP_AGE_MS, TIGHT_WINDOW_MS, MIN_TEXT_MATCH_SCORE, PROMPT_BLOCK_START, PROMPT_BLOCK_END, TASK_COMPLETE_HOOK_MARKERS, INTENT_MAP |
| `u_pj_s019_v003_d0404_λNU_βoc_entry_builders_seq022_v001.py` | 39 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_extract_composition_seq023_v001.py` | 46 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_force_fresh_seq019_v001.py` | 25 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_gemini_enricher_seq027_v001.py` | 52 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_intent_seq006_v001.py` | 10 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_meta_hook_builder_seq017_v001.py` | 44 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_meta_hook_seq005_v001.py` | 12 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_module_refs_seq007_v001.py` | 14 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_orchestrator_seq030_v001.py` | 45 | log_enriched_entry |
| `u_pj_s019_v003_d0404_λNU_βoc_post_append_seq026_v001.py` | 13 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_predict_issues_decomposed_seq014_v001.py` | 71 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_recent_bindings_seq008_v001.py` | 25 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_refresh_copilot_seq021_v001.py` | 51 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_refresh_utils_seq018_v001.py` | 46 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_running_stats_decomposed_seq013_v001.py` | 67 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_select_composition_seq010_v001.py` | 39 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_skip_duplicate_seq011_v001.py` | 17 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_staleness_alert_seq029_v001.py` | 15 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_telemetry_loaders_seq012_v001.py` | 48 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_text_matching_seq003_v001.py` | 38 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_training_pair_seq028_v001.py` | 21 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_utils_seq002_v001.py` | 52 🟡 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_write_raw_seq024_v001.py` | 21 | — |
| `u_pj_s019_v003_d0404_λNU_βoc_write_snapshot_seq020_v001.py` | 9 | — |

---

## EXPORTS

`COMPS_PATH, COPILOT_PATH, EDIT_PAIRS, HEAT_PATH, INTENT_MAP, JOURNAL_PATH, MAX_COMP_AGE_MS, MIN_TEXT_MATCH_SCORE, MUTATIONS_PATH, PROFILE_PATH, PROMPT_BLOCK_END, PROMPT_BLOCK_START, PROMPT_COMPS_PATH, SNAPSHOT_PATH, TASK_COMPLETE_HOOK_MARKERS, TASK_PATH, TIGHT_WINDOW_MS, log_enriched_entry`

---

## STRUCTURE

```
u_pj_s019_v003_d0404_λNU_βoc/
  ├── __init__.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_append_journal_seq025_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_build_snapshot_decomposed_seq015_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_candidate_comps_seq009_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_coaching_seq016_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_composition_key_seq004_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_constants_seq001_v001.py  (JOURNAL_PATH, SNAPSHOT_PATH, COMPS_PATH)
  ├── u_pj_s019_v003_d0404_λNU_βoc_entry_builders_seq022_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_extract_composition_seq023_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_force_fresh_seq019_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_gemini_enricher_seq027_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_intent_seq006_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_meta_hook_builder_seq017_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_meta_hook_seq005_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_module_refs_seq007_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_orchestrator_seq030_v001.py  (log_enriched_entry)
  ├── u_pj_s019_v003_d0404_λNU_βoc_post_append_seq026_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_predict_issues_decomposed_seq014_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_recent_bindings_seq008_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_refresh_copilot_seq021_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_refresh_utils_seq018_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_running_stats_decomposed_seq013_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_select_composition_seq010_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_skip_duplicate_seq011_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_staleness_alert_seq029_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_telemetry_loaders_seq012_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_text_matching_seq003_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_training_pair_seq028_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_utils_seq002_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_write_raw_seq024_v001.py
  ├── u_pj_s019_v003_d0404_λNU_βoc_write_snapshot_seq020_v001.py
  └── MANIFEST.md
```

---

## 📦 PROMPT BOX — U_PJ_S019_V003_D0404_ΛNU_ΒOC TASKS
*Generated by Pigeon Compiler | 2026-04-13*

- [ ] **U_PJ_S019_V003_D0404_ΛNU_ΒOC-001**: Verify all imports resolve correctly
- [ ] **U_PJ_S019_V003_D0404_ΛNU_ΒOC-002**: Run drift watcher on this folder
- [ ] **U_PJ_S019_V003_D0404_ΛNU_ΒOC-003**: Add unit tests for extracted functions
- [ ] **U_PJ_S019_V003_D0404_ΛNU_ΒOC-004**: Verify no circular imports
- [ ] **U_PJ_S019_V003_D0404_ΛNU_ΒOC-005**: Integration test with parent package

---

## CHANGELOG

### v1.0.0 (2026-04-13)
- **Source**: `u_pj_s019_v003_d0404_λNU_βoc.py` → 31 files, 1020 total lines
- **Status**: ✅ ALL COMPLIANT
- **Cost**: $0.0051
- **Timestamp**: 2026-04-13 22:15

