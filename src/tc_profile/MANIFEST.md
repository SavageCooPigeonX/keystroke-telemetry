# tc_profile/ MANIFEST.md
## Pigeon-Extracted from `tc_profile.py`
**Version**: v1.0.0 | **Last Updated**: 2026-04-13

---

## FILES

| File | Lines | Functions |
|------|-------|-----------|
| `__init__.py` | 17 | — |
| `tc_profile_bootstrap_completions_seq035_v001.py` | 3 | — |
| `tc_profile_bootstrap_compositions_seq034_v001.py` | 3 | — |
| `tc_profile_bootstrap_decomposed_seq033_v001.py` | 180 🟡 | bootstrap_profile |
| `tc_profile_bootstrap_finalize_seq036_v001.py` | 180 🟡 | bootstrap_profile |
| `tc_profile_constants_seq001_v001.py` | 64 🟡 | PROFILE_PATH, _SECTION_SIGNALS, _INTENT_STOPWORDS |
| `tc_profile_empty_profile_decomposed_seq004_v001.py` | 102 🟡 | — |
| `tc_profile_empty_section_decomposed_seq005_v001.py` | 94 🟡 | — |
| `tc_profile_empty_structs_seq003_v001.py` | 193 🟡 | — |
| `tc_profile_format_intelligence_decomposed_seq025_v001.py` | 62 🟡 | format_intelligence_for_prompt |
| `tc_profile_format_profile_decomposed_seq037_v001.py` | 103 🟡 | format_profile_for_prompt |
| `tc_profile_generate_journal_seq043_v001.py` | 26 | generate_profile_from_journal |
| `tc_profile_generate_session_decomposed_seq042_v001.py` | 57 🟡 | generate_profile_from_session |
| `tc_profile_generate_session_seq041_v001.py` | 57 🟡 | generate_profile_from_session |
| `tc_profile_intelligence_behavioral_laws_seq022_v001.py` | 19 | — |
| `tc_profile_intelligence_comfort_seq010_v001.py` | 28 | — |
| `tc_profile_intelligence_contradiction_seq021_v001.py` | 37 | — |
| `tc_profile_intelligence_decision_seq019_v001.py` | 32 | — |
| `tc_profile_intelligence_decision_work_seq018_v001.py` | 59 🟡 | — |
| `tc_profile_intelligence_deductions_a_seq009_v001.py` | 109 🟡 | — |
| `tc_profile_intelligence_deductions_b_seq014_v001.py` | 121 🟡 | — |
| `tc_profile_intelligence_deductions_seq009_v001.py` | 194 🟡 | — |
| `tc_profile_intelligence_deductions_seq010_v001.py` | 26 | — |
| `tc_profile_intelligence_deletion_seq012_v001.py` | 43 | — |
| `tc_profile_intelligence_deletion_time_seq011_v001.py` | 82 🟡 | — |
| `tc_profile_intelligence_frustration_seq016_v001.py` | 38 | — |
| `tc_profile_intelligence_frustration_suppression_seq015_v001.py` | 63 🟡 | — |
| `tc_profile_intelligence_orchestrator_seq024_v001.py` | 37 | — |
| `tc_profile_intelligence_persist_seq023_v001.py` | 13 | — |
| `tc_profile_intelligence_suppression_seq017_v001.py` | 26 | — |
| `tc_profile_intelligence_time_seq013_v001.py` | 40 | — |
| `tc_profile_intelligence_work_seq020_v001.py` | 28 | — |
| `tc_profile_intent_extractors_seq039_v001.py` | 45 | extract_session_triggers, extract_session_files |
| `tc_profile_intent_generation_seq038_v001.py` | 65 🟡 | extract_session_triggers, extract_session_files, detect_session_template |
| `tc_profile_intent_template_seq040_v001.py` | 21 | detect_session_template |
| `tc_profile_load_save_seq030_v001.py` | 33 | load_profile, save_profile |
| `tc_profile_mine_code_style_analyzer_seq028_v001.py` | 3 | — |
| `tc_profile_mine_code_style_compiler_seq029_v001.py` | 149 🟡 | — |
| `tc_profile_mine_code_style_decomposed_seq026_v001.py` | 149 🟡 | — |
| `tc_profile_mine_code_style_scanner_seq027_v001.py` | 3 | — |
| `tc_profile_section_classify_seq006_v001.py` | 30 | classify_section |
| `tc_profile_state_seq002_v001.py` | 3 | — |
| `tc_profile_update_completion_decomposed_seq031_v001.py` | 141 🟡 | update_profile_from_completion |
| `tc_profile_update_composition_decomposed_seq032_v001.py` | 83 🟡 | update_profile_from_composition |
| `tc_profile_update_section_decomposed_seq007_v001.py` | 121 🟡 | update_section |

---

## EXPORTS

`PROFILE_PATH, _INTENT_STOPWORDS, _SECTION_SIGNALS, bootstrap_profile, bootstrap_profile, classify_section, detect_session_template, detect_session_template, extract_session_files, extract_session_files, extract_session_triggers, extract_session_triggers, format_intelligence_for_prompt, format_profile_for_prompt, generate_profile_from_journal, generate_profile_from_session, generate_profile_from_session, load_profile, save_profile, update_profile_from_completion, update_profile_from_composition, update_section`

---

## STRUCTURE

```
tc_profile/
  ├── __init__.py
  ├── tc_profile_bootstrap_completions_seq035_v001.py
  ├── tc_profile_bootstrap_compositions_seq034_v001.py
  ├── tc_profile_bootstrap_decomposed_seq033_v001.py  (bootstrap_profile)
  ├── tc_profile_bootstrap_finalize_seq036_v001.py  (bootstrap_profile)
  ├── tc_profile_constants_seq001_v001.py  (PROFILE_PATH, _SECTION_SIGNALS, _INTENT_STOPWORDS)
  ├── tc_profile_empty_profile_decomposed_seq004_v001.py
  ├── tc_profile_empty_section_decomposed_seq005_v001.py
  ├── tc_profile_empty_structs_seq003_v001.py
  ├── tc_profile_format_intelligence_decomposed_seq025_v001.py  (format_intelligence_for_prompt)
  ├── tc_profile_format_profile_decomposed_seq037_v001.py  (format_profile_for_prompt)
  ├── tc_profile_generate_journal_seq043_v001.py  (generate_profile_from_journal)
  ├── tc_profile_generate_session_decomposed_seq042_v001.py  (generate_profile_from_session)
  ├── tc_profile_generate_session_seq041_v001.py  (generate_profile_from_session)
  ├── tc_profile_intelligence_behavioral_laws_seq022_v001.py
  ├── tc_profile_intelligence_comfort_seq010_v001.py
  ├── tc_profile_intelligence_contradiction_seq021_v001.py
  ├── tc_profile_intelligence_decision_seq019_v001.py
  ├── tc_profile_intelligence_decision_work_seq018_v001.py
  ├── tc_profile_intelligence_deductions_a_seq009_v001.py
  ├── tc_profile_intelligence_deductions_b_seq014_v001.py
  ├── tc_profile_intelligence_deductions_seq009_v001.py
  ├── tc_profile_intelligence_deductions_seq010_v001.py
  ├── tc_profile_intelligence_deletion_seq012_v001.py
  ├── tc_profile_intelligence_deletion_time_seq011_v001.py
  ├── tc_profile_intelligence_frustration_seq016_v001.py
  ├── tc_profile_intelligence_frustration_suppression_seq015_v001.py
  ├── tc_profile_intelligence_orchestrator_seq024_v001.py
  ├── tc_profile_intelligence_persist_seq023_v001.py
  ├── tc_profile_intelligence_suppression_seq017_v001.py
  ├── tc_profile_intelligence_time_seq013_v001.py
  ├── tc_profile_intelligence_work_seq020_v001.py
  ├── tc_profile_intent_extractors_seq039_v001.py  (extract_session_triggers, extract_session_files)
  ├── tc_profile_intent_generation_seq038_v001.py  (extract_session_triggers, extract_session_files, detect_session_template)
  ├── tc_profile_intent_template_seq040_v001.py  (detect_session_template)
  ├── tc_profile_load_save_seq030_v001.py  (load_profile, save_profile)
  ├── tc_profile_mine_code_style_analyzer_seq028_v001.py
  ├── tc_profile_mine_code_style_compiler_seq029_v001.py
  ├── tc_profile_mine_code_style_decomposed_seq026_v001.py
  ├── tc_profile_mine_code_style_scanner_seq027_v001.py
  ├── tc_profile_section_classify_seq006_v001.py  (classify_section)
  ├── tc_profile_state_seq002_v001.py
  ├── tc_profile_update_completion_decomposed_seq031_v001.py  (update_profile_from_completion)
  ├── tc_profile_update_composition_decomposed_seq032_v001.py  (update_profile_from_composition)
  ├── tc_profile_update_section_decomposed_seq007_v001.py  (update_section)
  └── MANIFEST.md
```

---

## 📦 PROMPT BOX — TC_PROFILE TASKS
*Generated by Pigeon Compiler | 2026-04-13*

- [ ] **TC_PROFILE-001**: Verify all imports resolve correctly
- [ ] **TC_PROFILE-002**: Run drift watcher on this folder
- [ ] **TC_PROFILE-003**: Add unit tests for extracted functions
- [ ] **TC_PROFILE-004**: Verify no circular imports
- [ ] **TC_PROFILE-005**: Integration test with parent package

---

## CHANGELOG

### v1.0.0 (2026-04-13)
- **Source**: `tc_profile.py` → 45 files, 2982 total lines
- **Status**: ✅ ALL COMPLIANT
- **Cost**: $0.0066
- **Timestamp**: 2026-04-13 22:19

