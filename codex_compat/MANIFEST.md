# codex_compat/ MANIFEST.md
## Pigeon-Extracted from `codex_compat.py`
**Version**: v1.0.0 | **Last Updated**: 2026-06-05

---

## FILES

| File | Lines | Functions |
|------|-------|-----------|
| `__init__.py` | 20 | — |
| `codex_compat_seq001_v001.py` | 49 | — |
| `codex_compat_seq002_v001.py` | 51 🟡 | — |
| `codex_compat_seq003_v001.py` | 36 | — |
| `codex_compat_seq004_v001.py` | 44 | — |
| `codex_compat_seq005_v001.py` | 46 | — |
| `codex_compat_seq006_v001.py` | 49 | train_numeric_surface, predict_numeric_files |
| `codex_compat_seq007_v001.py` | 56 🟡 | — |
| `codex_compat_seq008_v001.py` | 62 🟡 | — |
| `codex_compat_seq009_v001.py` | 41 | — |
| `codex_compat_seq010_v001.py` | 49 | — |
| `codex_compat_seq011_v001.py` | 69 🟡 | — |
| `codex_compat_seq012_v001.py` | 46 | — |
| `codex_compat_seq013_v001.py` | 36 | — |
| `codex_compat_seq014_v001.py` | 49 | — |
| `codex_compat_seq015_v001.py` | 39 | — |
| `codex_compat_seq016_v001.py` | 54 🟡 | — |
| `codex_compat_seq017_v001.py` | 48 | launch_deepseek_daemon |
| `codex_compat_seq018_v001.py` | 68 🟡 | enqueue_deepseek_prompt_job |
| `codex_compat_seq019_v001.py` | 74 🟡 | — |
| `codex_compat_seq020_v001.py` | 57 🟡 | — |
| `codex_compat_seq021_v001.py` | 30 | — |
| `codex_compat_seq022_v001.py` | 162 🟡 | build_dynamic_context_pack |
| `codex_compat_seq023_v001.py` | 198 🟡 | — |
| `codex_compat_seq024_v001.py` | 48 | — |
| `codex_compat_seq025_v001.py` | 52 🟡 | — |
| `codex_compat_seq026_v001.py` | 62 🟡 | close_intent_loop, get_intent_loop_status |
| `codex_compat_seq027_v001.py` | 89 🟡 | audit_stale_dates |
| `codex_compat_seq028_v001.py` | 122 🟡 | run_pre_prompt_from_composition |
| `codex_compat_seq029_v001.py` | 158 🟡 | run_pre_prompt_pipeline |
| `codex_compat_seq030_v001.py` | 57 🟡 | select_context |
| `codex_compat_seq031_v001.py` | 65 🟡 | refresh_state |
| `codex_compat_seq032_v001.py` | 150 🟡 | — |
| `codex_compat_seq033_v001.py` | 49 | — |
| `codex_compat_seq034_v001.py` | 128 🟡 | log_prompt |
| `codex_compat_seq035_v001.py` | 61 🟡 | log_composition |
| `codex_compat_seq036_v001.py` | 44 | — |
| `codex_compat_seq037_v001.py` | 80 🟡 | log_response |
| `codex_compat_seq038_v001.py` | 19 | — |
| `codex_compat_seq039_v001.py` | 59 🟡 | log_edit |
| `codex_compat_seq040_v001.py` | 43 | capture_pair, record_entropy_shed |
| `codex_compat_seq041_v001.py` | 40 | push_intent_resolver |
| `codex_compat_seq042_v001.py` | 61 🟡 | import_jsonl |
| `codex_compat_seq043_v001.py` | 135 🟡 | build_parser |
| `codex_compat_seq044_v001.py` | 168 🟡 | main |

---

## EXPORTS

`audit_stale_dates, build_dynamic_context_pack, build_parser, capture_pair, close_intent_loop, enqueue_deepseek_prompt_job, get_intent_loop_status, import_jsonl, launch_deepseek_daemon, log_composition, log_edit, log_prompt, log_response, main, predict_numeric_files, push_intent_resolver, record_entropy_shed, refresh_state, run_pre_prompt_from_composition, run_pre_prompt_pipeline, select_context, train_numeric_surface`

---

## STRUCTURE

```
codex_compat/
  ├── __init__.py
  ├── codex_compat_seq001_v001.py
  ├── codex_compat_seq002_v001.py
  ├── codex_compat_seq003_v001.py
  ├── codex_compat_seq004_v001.py
  ├── codex_compat_seq005_v001.py
  ├── codex_compat_seq006_v001.py  (train_numeric_surface, predict_numeric_files)
  ├── codex_compat_seq007_v001.py
  ├── codex_compat_seq008_v001.py
  ├── codex_compat_seq009_v001.py
  ├── codex_compat_seq010_v001.py
  ├── codex_compat_seq011_v001.py
  ├── codex_compat_seq012_v001.py
  ├── codex_compat_seq013_v001.py
  ├── codex_compat_seq014_v001.py
  ├── codex_compat_seq015_v001.py
  ├── codex_compat_seq016_v001.py
  ├── codex_compat_seq017_v001.py  (launch_deepseek_daemon)
  ├── codex_compat_seq018_v001.py  (enqueue_deepseek_prompt_job)
  ├── codex_compat_seq019_v001.py
  ├── codex_compat_seq020_v001.py
  ├── codex_compat_seq021_v001.py
  ├── codex_compat_seq022_v001.py  (build_dynamic_context_pack)
  ├── codex_compat_seq023_v001.py
  ├── codex_compat_seq024_v001.py
  ├── codex_compat_seq025_v001.py
  ├── codex_compat_seq026_v001.py  (close_intent_loop, get_intent_loop_status)
  ├── codex_compat_seq027_v001.py  (audit_stale_dates)
  ├── codex_compat_seq028_v001.py  (run_pre_prompt_from_composition)
  ├── codex_compat_seq029_v001.py  (run_pre_prompt_pipeline)
  ├── codex_compat_seq030_v001.py  (select_context)
  ├── codex_compat_seq031_v001.py  (refresh_state)
  ├── codex_compat_seq032_v001.py
  ├── codex_compat_seq033_v001.py
  ├── codex_compat_seq034_v001.py  (log_prompt)
  ├── codex_compat_seq035_v001.py  (log_composition)
  ├── codex_compat_seq036_v001.py
  ├── codex_compat_seq037_v001.py  (log_response)
  ├── codex_compat_seq038_v001.py
  ├── codex_compat_seq039_v001.py  (log_edit)
  ├── codex_compat_seq040_v001.py  (capture_pair, record_entropy_shed)
  ├── codex_compat_seq041_v001.py  (push_intent_resolver)
  ├── codex_compat_seq042_v001.py  (import_jsonl)
  ├── codex_compat_seq043_v001.py  (build_parser)
  ├── codex_compat_seq044_v001.py  (main)
  └── MANIFEST.md
```

---

## 📦 PROMPT BOX — CODEX_COMPAT TASKS
*Generated by Pigeon Compiler | 2026-06-05*

- [ ] **CODEX_COMPAT-001**: Verify all imports resolve correctly
- [ ] **CODEX_COMPAT-002**: Run drift watcher on this folder
- [ ] **CODEX_COMPAT-003**: Add unit tests for extracted functions
- [ ] **CODEX_COMPAT-004**: Verify no circular imports
- [ ] **CODEX_COMPAT-005**: Integration test with parent package

---

## CHANGELOG

### v1.0.0 (2026-06-05)
- **Source**: `codex_compat.py` → 45 files, 3123 total lines
- **Status**: ✅ ALL COMPLIANT
- **Cost**: $0.0000
- **Timestamp**: 2026-06-05 17:48

